import pytest

from powercontrollab import PlantConfig, SimulationConfig


def test_requested_ac_voltage_requires_dc_headroom():
    # 280 Vrms needs about 396 V peak, above the 392 V modulation headroom.
    with pytest.raises(ValueError, match="Reference peak"):
        PlantConfig(dc_voltage=400, voltage_rms=280)
    feasible = PlantConfig(dc_voltage=400, voltage_rms=270)
    assert feasible.peak < 392


def test_load_step_analysis_has_a_full_cycle_after_event():
    plant = PlantConfig()
    # Five analysis cycles starting at the event itself are too early.
    with pytest.raises(ValueError, match="analysis needs a full cycle"):
        SimulationConfig(scenario="load-step", duration=0.20).validate_for(plant)
    # At 50 Hz, 220 ms leaves [120, 220) ms after the event at 100 ms.
    SimulationConfig(scenario="load-step", duration=0.22).validate_for(plant)
