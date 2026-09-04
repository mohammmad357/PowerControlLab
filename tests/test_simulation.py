from dataclasses import replace

import numpy as np
import pytest

from powercontrollab import PlantConfig, SimulationConfig, simulate
from powercontrollab.analysis import compute_metrics
from powercontrollab.controllers import CONTROLLERS
from powercontrollab.scenarios import operating_point

SHORT = SimulationConfig(duration=0.08, analysis_cycles=1)


@pytest.mark.parametrize("controller", CONTROLLERS)
def test_nominal_controllers_track_and_respect_actuator(controller):
    result = simulate(controller, config=SHORT)
    metrics = compute_metrics(result)
    assert np.all(np.isfinite(result.voltage))
    assert metrics["steady_rmse_v"] < 12
    assert abs(metrics["output_rms_v"] - 230) < 10
    assert np.max(abs(result.modulation)) <= result.plant.modulation_limit
    assert metrics["solver_fallbacks"] == 0


def test_noise_is_reproducible_and_seed_changes_result():
    config = replace(SHORT, scenario="noise")
    a, b = simulate(config=config), simulate(config=config)
    c = simulate(config=replace(config, seed=8))
    np.testing.assert_array_equal(a.voltage, b.voltage)
    assert not np.array_equal(a.voltage, c.voltage)


def test_delay_is_exactly_one_command_sample():
    result = simulate(config=replace(SHORT, scenario="delay"))
    n = result.config.substeps
    np.testing.assert_array_equal(
        result.modulation[n:-1:n], result.commanded_modulation[: -n - 1 : n]
    )
    assert np.all(result.modulation[:n] == 0)


def test_parameter_mismatch_does_not_change_controller_nominal_parameters():
    plant = PlantConfig()
    point = operating_point(plant, replace(SHORT, scenario="mismatch"), 0)
    assert point.inductance == pytest.approx(1.3 * plant.inductance)
    assert point.capacitance == pytest.approx(0.8 * plant.capacitance)
    assert plant.inductance == 0.002


def test_step_is_applied_at_configured_event():
    p, cfg = PlantConfig(), SimulationConfig(scenario="load-step")
    assert operating_point(p, cfg, cfg.event_time - p.period).resistance == 50
    assert operating_point(p, cfg, cfg.event_time).resistance == 25


def test_switching_agrees_with_averaged_fundamental():
    average = compute_metrics(simulate(config=SHORT))
    switched = compute_metrics(simulate(config=replace(SHORT, mode="switching")))
    assert abs(switched["fundamental_rms_v"] - average["fundamental_rms_v"]) < 3
    assert switched["broadband_residual_rms_v"] > average["broadband_residual_rms_v"]


def test_nonlinear_rk4_converges_with_refinement():
    coarse = simulate("mpc", config=replace(SHORT, scenario="nonlinear"))
    fine = simulate("mpc", config=replace(SHORT, scenario="nonlinear", substeps=20))
    assert np.max(np.abs(coarse.voltage - fine.voltage[::2])) < 0.2
    assert np.min(fine.rectifier_voltage) >= -1e-8


@pytest.mark.parametrize(
    "kwargs",
    [
        {"duration": float("nan")},
        {"substeps": 0},
        {"substeps": 3.5},
        {"seed": -1},
        {"mode": "magic"},
        {"current_noise_std": -1},
    ],
)
def test_invalid_simulation_configuration(kwargs):
    with pytest.raises(ValueError):
        SimulationConfig(**kwargs)


def test_short_or_incoherent_analysis_fails_early():
    with pytest.raises(ValueError):
        simulate(config=SimulationConfig(duration=0.04))
    with pytest.raises(ValueError):
        simulate(config=SimulationConfig(duration=0.241))
