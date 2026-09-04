"""Passive resistive and diode-bridge/RC load models."""

from math import copysign


def diode_current(voltage: float, rectifier_voltage: float, plant) -> float:
    """DC-side conduction through two diodes and a finite source resistance."""
    return max(
        (abs(voltage) - rectifier_voltage - 2 * plant.diode_drop)
        / plant.rectifier_series_resistance,
        0.0,
    )


def load_current(voltage, rectifier_voltage, resistance, plant, nonlinear=False):
    current = voltage / resistance
    if nonlinear:
        current += copysign(diode_current(voltage, rectifier_voltage, plant), voltage)
    return current
