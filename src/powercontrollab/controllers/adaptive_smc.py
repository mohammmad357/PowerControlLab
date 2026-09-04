"""Bounded adaptive switching gain with dead zone and leakage (empirical design)."""

from dataclasses import dataclass

from .smc import SMCController


@dataclass(frozen=True)
class AdaptationGains:
    minimum: float = 6.0  # V
    maximum: float = 25.0  # V
    growth: float = 450.0  # V/s per normalized excess
    leakage: float = 8.0  # 1/s
    dead_zone: float = 0.15


class AdaptiveSMCController(SMCController):
    name = "adaptive-smc"

    def __init__(self, plant, ramp_time=0.02, gains=None, adaptation=None):
        super().__init__(plant, ramp_time, gains)
        self.adaptation = adaptation or AdaptationGains()
        self.gain = self.adaptation.minimum

    def update_gain(self, surface):
        a = self.adaptation
        excess = max(abs(surface) / self.gains.boundary_width - a.dead_zone, 0)
        rate = a.growth * excess - a.leakage * (self.gain - a.minimum)
        self.gain = min(a.maximum, max(a.minimum, self.gain + self.plant.period * rate))
        return self.gain
