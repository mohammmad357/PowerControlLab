from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.optimize import minimize

from powercontrollab import PlantConfig
from powercontrollab.controllers.adaptive_smc import AdaptiveSMCController
from powercontrollab.controllers.base import Measurement
from powercontrollab.controllers.mpc import MPCController, MPCGains
from powercontrollab.controllers.pi import PIController


def test_mpc_matches_independent_optimizer():
    controller = MPCController(PlantConfig(), gains=replace(MPCGains(), horizon=5))
    measured = Measurement(300, 3, 6, 360)
    q, lo, hi = controller.problem_vectors(0.025, measured)
    matrix = controller.hessian
    independent = minimize(
        lambda u: u @ matrix @ u + q @ u,
        np.zeros(5),
        jac=lambda u: 2 * matrix @ u + q,
        bounds=list(zip(lo, hi, strict=True)),
        method="L-BFGS-B",
        options={"ftol": 1e-13, "gtol": 1e-9, "maxiter": 1000},
    )
    calculated = controller.step(0.025, measured)
    assert independent.success
    assert controller.fallbacks == 0
    assert calculated == pytest.approx(independent.x[0], abs=0.03)


def test_mpc_solver_failure_is_counted_and_bounded(monkeypatch):
    controller = MPCController(PlantConfig())
    failure = SimpleNamespace(
        info=SimpleNamespace(status="failed", status_val=7, iter=1000), x=None
    )
    monkeypatch.setattr(controller.solver, "solve", lambda **kwargs: failure)
    voltage = controller.step(0.027, Measurement(-100, -20, 0, 360))
    assert controller.fallbacks == 1
    assert np.isfinite(voltage) and abs(voltage) <= 360 * 0.98


def test_adaptive_gain_grows_and_relaxes_within_bounds():
    controller = AdaptiveSMCController(PlantConfig())
    for _ in range(1000):
        controller.update_gain(1e7)
    assert controller.gain == controller.adaptation.maximum
    for _ in range(1000):
        controller.update_gain(0)
    assert controller.adaptation.minimum <= controller.gain < controller.adaptation.maximum


def test_pi_antiwindup_under_unattainable_command():
    controller = PIController(PlantConfig())
    for _ in range(1000):
        controller.step(0.025, Measurement(-500, -100, 0, 100))
    assert controller.voltage_integral == 0
    assert controller.current_integral == 0
