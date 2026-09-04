import numpy as np
import pytest
from scipy.linalg import expm

from powercontrollab import PlantConfig, SimulationConfig
from powercontrollab.models.inverter import derivative, rk4_step
from powercontrollab.models.lc_filter import continuous_matrices
from powercontrollab.models.loads import diode_current
from powercontrollab.modulation.spwm import segments
from powercontrollab.reference import reference
from powercontrollab.scenarios import operating_point


def test_rk4_agrees_with_independent_matrix_exponential():
    plant = PlantConfig()
    op = operating_point(plant, SimulationConfig(), 0)
    a, b = continuous_matrices(
        op.inductance, op.capacitance, op.resistance, plant.inductor_resistance
    )
    augmented = np.zeros((3, 3))
    augmented[:2, :2] = a
    augmented[:2, 2] = b[:, 0] * 180
    initial = np.array([1.2, 45.0, 1.0])
    dt = 5e-6
    expected = (expm(augmented * dt) @ initial)[:2]
    calculated = rk4_step((initial[0], initial[1], 0), 180, dt, op, plant)[:2]
    np.testing.assert_allclose(calculated, expected, rtol=1e-8, atol=2e-7)


@pytest.mark.parametrize("nonlinear", [False, True])
def test_instantaneous_energy_balance(nonlinear):
    p = PlantConfig()
    op = operating_point(p, SimulationConfig(), 0)
    current, voltage, rectifier_voltage = 4.0, 250.0, 240.0
    di, dv, dr = derivative((current, voltage, rectifier_voltage), 280, op, p, nonlinear)
    stored_power = op.inductance * current * di + op.capacitance * voltage * dv
    diode_loss = 0.0
    if nonlinear:
        stored_power += p.rectifier_capacitance * rectifier_voltage * dr
        conduction = diode_current(voltage, rectifier_voltage, p)
        diode_loss = (
            2 * p.diode_drop * conduction
            + p.rectifier_series_resistance * conduction**2
            + rectifier_voltage**2 / p.rectifier_resistance
        )
    expected = (
        280 * current - p.inductor_resistance * current**2 - voltage**2 / op.resistance - diode_loss
    )
    assert stored_power == pytest.approx(expected, abs=1e-10)


@pytest.mark.parametrize("modulation", [-1, -0.981, -0.71, -0.03, 0, 0.007, 0.435, 0.98, 1])
def test_pwm_period_average_equals_command(modulation):
    integral = sum(
        fraction * level
        for k in range(10)
        for fraction, level in segments(modulation, k / 10, (k + 1) / 10)
    )
    assert integral == pytest.approx(modulation, abs=2e-15)


def test_reference_derivatives_are_consistent():
    p = PlantConfig()
    for t in [0.003, 0.012, 0.02, 0.033]:
        epsilon = 1e-7
        left = reference(t - epsilon, p, 0.02)
        right = reference(t + epsilon, p, 0.02)
        center = reference(t, p, 0.02)
        assert (right[0] - left[0]) / (2 * epsilon) == pytest.approx(center[1], rel=1e-6, abs=0.01)
        assert (right[1] - left[1]) / (2 * epsilon) == pytest.approx(center[2], rel=2e-4, abs=150)
