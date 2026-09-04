"""Three-state plant and explicit RK4 integrator (switching edges resolved externally)."""

from math import copysign

from .loads import diode_current


def derivative(state, bridge_voltage, operating, plant, nonlinear=False):
    current, voltage, rectifier_voltage = state
    rectified = diode_current(voltage, rectifier_voltage, plant) if nonlinear else 0.0
    output_current = voltage / operating.resistance + copysign(rectified, voltage)
    di = (bridge_voltage - voltage - plant.inductor_resistance * current) / operating.inductance
    dv = (current - output_current) / operating.capacitance
    dr = (
        ((rectified - rectifier_voltage / plant.rectifier_resistance) / plant.rectifier_capacitance)
        if nonlinear
        else 0.0
    )
    return di, dv, dr


def rk4_step(state, voltage, dt, operating, plant, nonlinear=False):
    k1 = derivative(state, voltage, operating, plant, nonlinear)
    k2 = derivative(
        tuple(x + dt * k / 2 for x, k in zip(state, k1, strict=True)),
        voltage,
        operating,
        plant,
        nonlinear,
    )
    k3 = derivative(
        tuple(x + dt * k / 2 for x, k in zip(state, k2, strict=True)),
        voltage,
        operating,
        plant,
        nonlinear,
    )
    k4 = derivative(
        tuple(x + dt * k for x, k in zip(state, k3, strict=True)),
        voltage,
        operating,
        plant,
        nonlinear,
    )
    return tuple(
        x + dt * (a + 2 * b + 2 * c + d) / 6
        for x, a, b, c, d in zip(state, k1, k2, k3, k4, strict=True)
    )
