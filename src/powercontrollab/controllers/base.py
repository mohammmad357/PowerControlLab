"""Controller contract: identical measurements and actuator limits for every method."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Measurement:
    voltage: float
    current: float
    load_current: float
    dc_voltage: float


class Controller:
    name = "base"

    def __init__(self, plant, ramp_time=0.02):
        self.plant = plant
        self.ramp_time = ramp_time
        self.saturations = 0
        self.fallbacks = 0
        self.diagnostic = 0.0

    def step(self, time: float, measured: Measurement) -> float:
        """Return desired bridge voltage, before the common actuator limiter."""
        raise NotImplementedError

    def clip(self, voltage, measured):
        limit = self.plant.modulation_limit * measured.dc_voltage
        return max(-limit, min(limit, voltage))
