import pytest

from powercontrollab import PlantConfig, SimulationConfig
from powercontrollab.scenarios import operating_point


@pytest.mark.parametrize(
    ("scenario", "dc_after", "resistance_after", "inductance", "capacitance"),
    [
        ("nominal", 400, 50, 0.002, 20e-6),
        ("load-step", 400, 25, 0.002, 20e-6),
        ("dc-sag", 360, 50, 0.002, 20e-6),
        ("mismatch", 400, 50, 0.0026, 16e-6),
        ("combined", 360, 25, 0.0026, 16e-6),
    ],
)
def test_disturbances_change_only_their_selected_parameters(
    scenario, dc_after, resistance_after, inductance, capacitance
):
    plant = PlantConfig()
    config = SimulationConfig(scenario=scenario)
    before = operating_point(plant, config, config.event_time - plant.period)
    at_event = operating_point(plant, config, config.event_time)
    later = operating_point(plant, config, config.event_time + plant.period)
    assert before.dc == 400
    assert before.resistance == 50
    for point in (before, at_event, later):
        assert point.inductance == pytest.approx(inductance)
        assert point.capacitance == pytest.approx(capacitance)
    for point in (at_event, later):
        assert point.dc == pytest.approx(dc_after)
        assert point.resistance == pytest.approx(resistance_after)
    assert plant == PlantConfig()
