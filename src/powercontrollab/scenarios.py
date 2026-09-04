"""Disturbances are applied to the plant; controller parameters stay nominal."""

from dataclasses import dataclass

SCENARIOS = {
    "nominal": "Resistive load, nominal parameters",
    "load-step": "Load resistance drops by 50% at 100 ms",
    "dc-sag": "DC bus drops by 10% at 100 ms",
    "noise": "Seeded Gaussian voltage and current sensor noise",
    "mismatch": "L +30%, C -20% from startup; nominal controller model",
    "delay": "One controller-sample actuator delay from startup",
    "nonlinear": "Diode bridge with an RC DC load in parallel with R",
    "combined": "Load step, DC sag, noise, mismatch and actuator delay",
}


@dataclass(frozen=True)
class OperatingPoint:
    dc: float
    resistance: float
    inductance: float
    capacitance: float


def operating_point(plant, config, time: float) -> OperatingPoint:
    after = time >= config.event_time - 1e-12
    scenario = config.scenario
    mismatch = scenario in ("mismatch", "combined")
    return OperatingPoint(
        dc=plant.dc_voltage
        * (config.dc_sag_factor if after and scenario in ("dc-sag", "combined") else 1),
        resistance=plant.load_resistance
        * (config.load_step_factor if after and scenario in ("load-step", "combined") else 1),
        inductance=plant.inductance * (config.inductance_factor if mismatch else 1),
        capacitance=plant.capacitance * (config.capacitance_factor if mismatch else 1),
    )
