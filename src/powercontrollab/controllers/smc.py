"""Sampled boundary-layer SMC using an exact nominal discrete reaching-law inversion."""

from dataclasses import dataclass

import numpy as np

from ..models.lc_filter import discrete_matrices
from ..reference import reference
from .base import Controller


@dataclass(frozen=True)
class SMCGains:
    sliding_rate: float = 8000.0  # 1/s
    boundary_width: float = 50000.0  # V/s
    switching_gain: float = 18.0  # V


class SMCController(Controller):
    name = "smc"

    def __init__(self, plant, ramp_time=0.02, gains=None):
        super().__init__(plant, ramp_time)
        self.gains = gains or SMCGains()
        self.gain = self.gains.switching_gain
        g = self.gains
        if min(g.sliding_rate, g.boundary_width, g.switching_gain) <= 0:
            raise ValueError("SMC gains must be positive")
        self.ad, self.bd = discrete_matrices(plant)
        self.surface_vector = np.array(
            [
                1 / plant.capacitance,
                g.sliding_rate - 1 / (plant.load_resistance * plant.capacitance),
            ]
        )
        self.input_sensitivity = float(self.surface_vector @ self.bd[:, 0])

    def update_gain(self, surface):
        return self.gain

    def step(self, time, measured):
        p, g = self.plant, self.gains
        r, rd, _ = reference(time, p, self.ramp_time)
        error = r - measured.voltage
        error_rate = rd - (measured.current - measured.load_current) / p.capacitance
        surface = error_rate + g.sliding_rate * error
        gain = self.update_gain(surface)
        self.diagnostic = gain
        target_surface = surface - p.period * gain / (p.inductance * p.capacitance) * max(
            -1.0, min(1.0, surface / g.boundary_width)
        )
        next_r, next_rd, _ = reference(time + p.period, p, self.ramp_time)
        disturbance = measured.load_current - measured.voltage / p.load_resistance
        free = self.ad @ [measured.current, measured.voltage] + self.bd[:, 1] * disturbance
        free_surface = (
            next_rd
            + g.sliding_rate * next_r
            + disturbance / p.capacitance
            - self.surface_vector @ free
        )
        return float((free_surface - target_surface) / self.input_sensitivity)
