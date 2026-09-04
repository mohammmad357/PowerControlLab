"""Causal sampled-data simulation, with the same observations for all controllers."""

from collections import deque
from dataclasses import asdict, dataclass, field
from time import perf_counter

import numpy as np

from .config import PlantConfig, SimulationConfig
from .controllers import make_controller
from .controllers.base import Measurement
from .models.inverter import rk4_step
from .models.loads import load_current
from .modulation.spwm import segments
from .reference import reference
from .scenarios import operating_point


@dataclass
class SimulationResult:
    controller: str
    plant: PlantConfig
    config: SimulationConfig
    time: np.ndarray
    voltage: np.ndarray
    current: np.ndarray
    reference: np.ndarray
    load_current: np.ndarray
    rectifier_voltage: np.ndarray
    modulation: np.ndarray
    commanded_modulation: np.ndarray
    bridge_voltage: np.ndarray
    dc_voltage: np.ndarray
    diagnostics: dict = field(default_factory=dict)
    controller_parameters: dict = field(default_factory=dict)

    def arrays(self):
        names = (
            "time",
            "voltage",
            "current",
            "reference",
            "load_current",
            "rectifier_voltage",
            "modulation",
            "commanded_modulation",
            "bridge_voltage",
            "dc_voltage",
        )
        return {name: getattr(self, name) for name in names}


def simulate(controller="smc", plant=None, config=None) -> SimulationResult:
    plant, config = plant or PlantConfig(), config or SimulationConfig()
    config.validate_for(plant)
    control = make_controller(controller, plant, config.ramp_time)
    cycles = round(config.duration / plant.period)
    steps = cycles * config.substeps
    dt = plant.period / config.substeps
    time = np.arange(steps + 1) * dt
    states = np.zeros((steps + 1, 3))
    refs = np.array([reference(t, plant, config.ramp_time)[0] for t in time])
    iload, modulation, commands, bridge, dc = (np.zeros(steps + 1) for _ in range(5))
    rng = np.random.default_rng(config.seed)
    # Generate all noise ahead of time: identical random draws for each controller.
    noise = rng.standard_normal((cycles, 3))
    noisy = config.scenario in ("noise", "combined")
    delay = config.delay_samples if config.scenario in ("delay", "combined") else 0
    queue = deque([0.0] * delay)
    nonlinear = config.load == "nonlinear" or config.scenario == "nonlinear"
    state = (0.0, 0.0, 0.0)
    compute_times, diagnostic_values = [], []
    start = perf_counter()
    for k in range(cycles):
        first = k * config.substeps
        now = k * plant.period
        op = operating_point(plant, config, now)
        true_load = load_current(state[1], state[2], op.resistance, plant, nonlinear)
        measurement = Measurement(
            state[1] + (noise[k, 0] * config.voltage_noise_std if noisy else 0),
            state[0] + (noise[k, 1] * config.current_noise_std if noisy else 0),
            true_load + (noise[k, 2] * config.current_noise_std if noisy else 0),
            op.dc,
        )
        tick = perf_counter()
        requested_voltage = control.step(now, measurement)
        compute_times.append(perf_counter() - tick)
        if not np.isfinite(requested_voltage):
            raise RuntimeError(f"{controller} returned a nonfinite command at {now:.6f} s")
        request = requested_voltage / op.dc
        command = max(-plant.modulation_limit, min(plant.modulation_limit, request))
        control.saturations += int(abs(request - command) > 1e-8)
        queue.append(command)
        applied = queue.popleft()
        diagnostic_values.append(control.diagnostic)
        for j in range(config.substeps):
            index = first + j
            modulation[index], commands[index], dc[index] = applied, command, op.dc
            iload[index] = load_current(state[1], state[2], op.resistance, plant, nonlinear)
            if config.mode == "averaged":
                bridge[index] = op.dc * applied
                state = rk4_step(state, bridge[index], dt, op, plant, nonlinear)
            else:
                average_bridge = 0.0
                for fraction, level in segments(
                    applied, j / config.substeps, (j + 1) / config.substeps
                ):
                    state = rk4_step(
                        state, op.dc * level, plant.period * fraction, op, plant, nonlinear
                    )
                    average_bridge += level * op.dc * fraction * config.substeps
                # Bin-average bridge voltage; states are instantaneous at bin boundaries.
                bridge[index] = average_bridge
            states[index + 1] = state
        if not np.all(np.isfinite(state)) or max(abs(x) for x in state) > 1e6:
            raise RuntimeError(f"Plant diverged at {now:.6f} s; inspect gains and integration step")
    op = operating_point(plant, config, time[-1])
    iload[-1] = load_current(state[1], state[2], op.resistance, plant, nonlinear)
    for array in (modulation, commands, bridge, dc):
        array[-1] = array[-2]
    diagnostics = {
        "wall_time_s": perf_counter() - start,
        "controller_median_us": float(np.median(compute_times) * 1e6),
        "controller_p99_us": float(np.percentile(compute_times, 99) * 1e6),
        "controller_samples": cycles,
        "clipped_requests": control.saturations,
        "solver_fallbacks": control.fallbacks,
        "diagnostic_min": float(min(diagnostic_values)),
        "diagnostic_max": float(max(diagnostic_values)),
        "actuator_delay_samples": delay,
        "effective_load": "nonlinear" if nonlinear else "resistive",
    }
    return SimulationResult(
        controller,
        plant,
        config,
        time,
        states[:, 1],
        states[:, 0],
        refs,
        iload,
        states[:, 2],
        modulation,
        commands,
        bridge,
        dc,
        diagnostics,
        {
            "gains": asdict(control.gains),
            **(
                {"adaptation": asdict(control.adaptation)} if hasattr(control, "adaptation") else {}
            ),
        },
    )
