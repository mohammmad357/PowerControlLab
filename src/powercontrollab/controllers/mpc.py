"""Condensed, constrained receding-horizon QP with a cached OSQP factorization."""

from dataclasses import dataclass

import numpy as np
import osqp
from scipy import sparse

from ..models.lc_filter import discrete_matrices
from ..reference import reference
from .base import Controller


@dataclass(frozen=True)
class MPCGains:
    horizon: int = 16
    voltage_weight: float = 1.0
    current_weight: float = 0.2
    input_weight: float = 0.01
    slew_weight: float = 0.02


class MPCController(Controller):
    name = "mpc"

    def __init__(self, plant, ramp_time=0.02, gains=None):
        super().__init__(plant, ramp_time)
        self.gains = gains or MPCGains()
        g, n = self.gains, self.gains.horizon
        if (
            n < 2
            or g.input_weight <= 0
            or min(g.voltage_weight, g.current_weight, g.slew_weight) < 0
        ):
            raise ValueError("MPC requires horizon >= 2 and valid convex cost weights")
        ad, bd = discrete_matrices(plant)
        powers = [np.linalg.matrix_power(ad, k) for k in range(n + 1)]
        self.f = np.vstack(powers[1:])
        self.g = np.zeros((2 * n, n))
        self.h = np.zeros(2 * n)
        for k in range(n):
            for j in range(k + 1):
                self.g[2 * k : 2 * k + 2, j] = powers[k - j] @ bd[:, 0]
                self.h[2 * k : 2 * k + 2] += powers[j] @ bd[:, 1]
        self.weights = np.tile([g.current_weight, g.voltage_weight], n)
        self.difference = np.eye(n) - np.eye(n, k=-1)
        self.hessian = (
            self.g.T @ (self.weights[:, None] * self.g)
            + g.input_weight * np.eye(n)
            + g.slew_weight * self.difference.T @ self.difference
        )
        bound = plant.modulation_limit * plant.dc_voltage
        self.solver = osqp.OSQP()
        self.solver.setup(
            P=sparse.csc_matrix(2 * self.hessian),
            q=np.zeros(n),
            A=sparse.eye(n, format="csc"),
            l=np.full(n, -bound),
            u=np.full(n, bound),
            verbose=False,
            warm_starting=True,
            eps_abs=1e-5,
            eps_rel=1e-5,
            max_iter=1000,
            adaptive_rho=False,
            polishing=False,
        )
        self.previous_voltage = 0.0
        self.last_status = "not run"

    def problem_vectors(self, time, measured):
        p, g = self.plant, self.gains
        # Measured load-current residual is held over the horizon, not future plant knowledge.
        disturbance = measured.load_current - measured.voltage / p.load_resistance
        references, feedforward = [], []
        for k in range(1, g.horizon + 1):
            r, rd, rdd = reference(time + k * p.period, p, self.ramp_time)
            references.extend([r / p.load_resistance + p.capacitance * rd + disturbance, r])
            # This is a regularization target. Tracking still uses the discrete prediction.
            feedforward.append(
                (1 + p.inductor_resistance / p.load_resistance) * r
                + (p.inductance / p.load_resistance + p.inductor_resistance * p.capacitance) * rd
                + p.inductance * p.capacitance * rdd
                + p.inductor_resistance * disturbance
            )
        free = self.f @ [measured.current, measured.voltage] + self.h * disturbance
        prior = np.zeros(g.horizon)
        prior[0] = self.previous_voltage
        q = 2 * (
            self.g.T @ (self.weights * (free - np.asarray(references)))
            - g.input_weight * np.asarray(feedforward)
            - g.slew_weight * self.difference.T @ prior
        )
        limit = p.modulation_limit * measured.dc_voltage
        return q, np.full(g.horizon, -limit), np.full(g.horizon, limit)

    def step(self, time, measured):
        q, lower, upper = self.problem_vectors(time, measured)
        self.solver.update(q=q, l=lower, u=upper)
        solution = self.solver.solve(raise_error=False)
        self.last_status = solution.info.status
        self.diagnostic = float(solution.info.iter)
        if (
            solution.info.status_val == 1
            and solution.x is not None
            and np.all(np.isfinite(solution.x))
        ):
            voltage = float(solution.x[0])
        else:
            # Failed/inaccurate QPs are visible in exported diagnostics, never silently accepted.
            self.fallbacks += 1
            p = self.plant
            r, rd, _ = reference(time, p, self.ramp_time)
            target = measured.load_current + p.capacitance * rd + 0.045 * (r - measured.voltage)
            voltage = measured.voltage + 8 * (target - measured.current)
        self.previous_voltage = self.clip(voltage, measured)
        return self.previous_voltage
