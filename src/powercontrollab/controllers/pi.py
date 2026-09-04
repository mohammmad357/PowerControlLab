"""Cascaded voltage/current PI with model feedforward and conditional anti-windup."""

from dataclasses import dataclass

from ..reference import reference
from .base import Controller


@dataclass(frozen=True)
class PIGains:
    voltage_kp: float = 0.08  # A/V
    voltage_ki: float = 30.0  # A/(V s)
    current_kp: float = 16.0  # V/A
    current_ki: float = 800.0  # V/(A s)


class PIController(Controller):
    name = "pi"

    def __init__(self, plant, ramp_time=0.02, gains=None):
        super().__init__(plant, ramp_time)
        self.gains = gains or PIGains()
        self.voltage_integral = 0.0
        self.current_integral = 0.0

    def step(self, time, measured):
        p, g = self.plant, self.gains
        r, rd, rdd = reference(time, p, self.ramp_time)
        error = r - measured.voltage
        next_vi = self.voltage_integral + error * p.period
        target_i = measured.load_current + p.capacitance * rd + g.voltage_kp * error
        target_i += g.voltage_ki * next_vi
        current_error = target_i - measured.current
        next_ci = self.current_integral + current_error * p.period
        feedforward = (
            measured.voltage
            + p.inductor_resistance * measured.current
            + p.inductance * (p.capacitance * rdd + rd / p.load_resistance)
        )
        voltage = feedforward + g.current_kp * current_error + g.current_ki * next_ci
        excess = voltage - self.clip(voltage, measured)
        # Freeze only an integrator whose increment would drive farther into saturation.
        if excess * error <= 0:
            self.voltage_integral = next_vi
        if excess * current_error <= 0:
            self.current_integral = next_ci
        return voltage
