"""Validated SI-unit configuration; nominal parameters are shared by all controllers."""

from dataclasses import dataclass, fields
from math import isfinite, pi, sqrt


@dataclass(frozen=True)
class PlantConfig:
    dc_voltage: float = 400.0
    voltage_rms: float = 230.0
    frequency: float = 50.0
    switching_frequency: float = 20_000.0
    inductance: float = 2e-3
    capacitance: float = 20e-6
    inductor_resistance: float = 0.15
    load_resistance: float = 50.0
    modulation_limit: float = 0.98
    rectifier_resistance: float = 100.0
    rectifier_capacitance: float = 470e-6
    rectifier_series_resistance: float = 3.0
    diode_drop: float = 0.7

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isfinite(value) or value <= 0:
                raise ValueError(f"{field.name} must be finite and positive")
        if not 0 < self.modulation_limit <= 1:
            raise ValueError("modulation_limit must be in (0, 1]")
        if self.voltage_rms * sqrt(2) >= self.dc_voltage * self.modulation_limit:
            raise ValueError("Reference peak must be below the nominal DC modulation headroom")
        if self.switching_frequency <= 80 * self.frequency:
            raise ValueError("switching_frequency must exceed 80 times the fundamental")
        if (
            abs(
                self.switching_frequency / self.frequency
                - round(self.switching_frequency / self.frequency)
            )
            > 1e-8
        ):
            raise ValueError("Use an integer number of controller samples per fundamental cycle")

    @property
    def period(self) -> float:
        return 1.0 / self.switching_frequency

    @property
    def peak(self) -> float:
        return self.voltage_rms * sqrt(2)

    @property
    def omega(self) -> float:
        return 2 * pi * self.frequency


@dataclass(frozen=True)
class SimulationConfig:
    duration: float = 0.24
    scenario: str = "nominal"
    load: str = "resistive"
    mode: str = "averaged"
    substeps: int = 10
    seed: int = 7
    event_time: float = 0.1
    ramp_time: float = 0.02
    analysis_cycles: int = 5
    voltage_noise_std: float = 0.5
    current_noise_std: float = 0.02
    delay_samples: int = 1
    dc_sag_factor: float = 0.9
    load_step_factor: float = 0.5
    inductance_factor: float = 1.3
    capacitance_factor: float = 0.8

    def __post_init__(self):
        from .scenarios import SCENARIOS

        if self.scenario not in SCENARIOS:
            raise ValueError(f"Unknown scenario {self.scenario!r}; choose from {tuple(SCENARIOS)}")
        if self.load not in ("resistive", "nonlinear"):
            raise ValueError("load must be resistive or nonlinear")
        if self.mode not in ("averaged", "switching"):
            raise ValueError("mode must be averaged or switching")
        for name in (
            "duration",
            "event_time",
            "ramp_time",
            "dc_sag_factor",
            "load_step_factor",
            "inductance_factor",
            "capacitance_factor",
        ):
            if not isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("voltage_noise_std", "current_noise_std"):
            if not isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        for name, minimum in (
            ("substeps", 2),
            ("analysis_cycles", 1),
            ("delay_samples", 0),
            ("seed", 0),
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")

    def validate_for(self, plant: PlantConfig):
        cycles = self.duration * plant.frequency
        if abs(cycles - round(cycles)) > 1e-8:
            raise ValueError("duration must contain an integer number of fundamental cycles")
        start = self.duration - self.analysis_cycles / plant.frequency
        disturbance = self.event_time if self.scenario in ("load-step", "dc-sag", "combined") else 0
        if start < max(self.ramp_time, disturbance) + 1 / plant.frequency - 1e-10:
            raise ValueError("Increase duration: analysis needs a full cycle after startup/events")
        if disturbance and self.event_time >= self.duration:
            raise ValueError("event_time must occur before the end of the run")
        if (
            disturbance
            and abs(self.event_time / plant.period - round(self.event_time / plant.period)) > 1e-8
        ):
            raise ValueError("event_time must align with a controller sample")
        dt = plant.period / self.substeps
        l_min = plant.inductance * min(1.0, self.inductance_factor)
        c_min = plant.capacitance * min(1.0, self.capacitance_factor)
        if dt > 0.05 * sqrt(l_min * c_min):
            raise ValueError("Increase substeps to resolve the LC dynamics")
        if (self.load == "nonlinear" or self.scenario == "nonlinear") and dt > (
            0.2 * plant.rectifier_series_resistance * c_min
        ):
            raise ValueError("Increase substeps to resolve diode conduction dynamics")
