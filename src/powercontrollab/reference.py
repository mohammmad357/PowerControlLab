"""Analytic sinusoidal reference with a twice differentiable quintic soft start."""

from math import cos, sin


def reference(time: float, plant, ramp_time: float) -> tuple[float, float, float]:
    """Return voltage, first derivative and second derivative in SI units."""
    q = min(1.0, max(0.0, time / ramp_time))
    envelope = 10 * q**3 - 15 * q**4 + 6 * q**5
    de = (30 * q**2 - 60 * q**3 + 30 * q**4) / ramp_time if 0 < q < 1 else 0.0
    dde = (60 * q - 180 * q**2 + 120 * q**3) / ramp_time**2 if 0 < q < 1 else 0.0
    s, c, w, a = sin(plant.omega * time), cos(plant.omega * time), plant.omega, plant.peak
    return (
        a * envelope * s,
        a * (de * s + envelope * w * c),
        a * (dde * s + 2 * de * w * c - envelope * w * w * s),
    )
