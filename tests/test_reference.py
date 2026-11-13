import numpy as np
import pytest

from powercontrollab import PlantConfig
from powercontrollab.reference import reference


def test_soft_start_begins_with_zero_voltage_velocity_and_acceleration():
    assert reference(0, PlantConfig(), 0.017) == (0, 0, 0)


@pytest.mark.parametrize("time", [0.017, 0.023, 0.041])
def test_reference_after_ramp_matches_unramped_sinusoid(time):
    # A non-cycle-aligned ramp prevents a zero crossing hiding endpoint errors.
    plant = PlantConfig()
    voltage, velocity, acceleration = reference(time, plant, 0.017)
    expected_voltage = plant.peak * np.sin(plant.omega * time)
    expected_velocity = plant.peak * plant.omega * np.cos(plant.omega * time)
    assert voltage == pytest.approx(expected_voltage, abs=1e-10)
    assert velocity == pytest.approx(expected_velocity, abs=1e-8)
    assert acceleration == pytest.approx(-plant.omega**2 * expected_voltage, abs=1e-6)
