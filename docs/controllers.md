# Controller laws and tuning

Each run creates fresh controller state. Every method has access to `v`, `i`, `i_load`,
`V_dc`, the same analytic reference, and the same nominal plant parameters. Tuning is fixed
across the benchmark scenarios. The defaults are illustrative engineering tunings, not
the result of an exhaustive or globally optimal tuning competition.

## Reference

The voltage reference is `r(t) = sqrt(2) V_rms a(t) sin(ωt)`. During startup,
`a = 10q³ − 15q⁴ + 6q⁵`, with `q = t/t_ramp` clipped to `[0,1]`.
The reference and its first two derivatives are continuous at the ramp boundaries.
All controllers use the same derivatives, calculated analytically.

## Cascaded PI

An outer voltage PI supplies a current command:

$$i^*=i_{load}+C\dot r+k_{pv}(r-v)+k_{iv}\int(r-v)dt.$$

An inner current PI supplies bridge voltage with nominal feedforward:

$$u=v+r_Li+L(C\ddot r+\dot r/R)+k_{pi}(i^*-i)+k_{ii}\int(i^*-i)dt.$$

The voltage gains are `0.08 A/V` and `30 A/(V s)`; current gains are `16 V/A` and
`800 V/(A s)`. Conditional anti-windup freezes each integrator only when its proposed
increment would drive the saturated command farther beyond the actuator bound.
This is a feedforward-assisted cascaded PI baseline, not a bare PI acting on an AC signal.

## Boundary-layer SMC

Use the nominal capacitor value to estimate voltage slope from measured currents:

$$e=r-v,\qquad\dot e=\dot r-\frac{i-i_{load}}{C},\qquad s=\dot e+\lambda e.$$

For a continuous nominal model, the equivalent-control derivation would give

$$u_{eq}=v+r_Li+L\{\dot r/R+C(\ddot r+\lambda\dot e)\},$$

$$u=u_{eq}+K\operatorname{sat}(s/\phi).$$

The implementation accounts for sampling explicitly. It imposes a discrete reaching law
`s_next = s − T K/(LC) sat(s/φ)` using the exact ZOH nominal plant. Let
`d = i_load − v/R`, `h = [1/C, λ − 1/(RC)]` and `x_free = A_d x + B_d d`. Then

$$u=\frac{\dot r_{next}+\lambda r_{next}+d/C-hx_{free}-s_{next}}{hB_u}.$$

This is a scalar algebraic inversion, not an optimization problem. The measured load
residual is held for one step; reference preview is analytic. Defaults are `λ = 8000 s⁻¹`,
`φ = 50000 V/s`, and `K = 18 V`. For the nominal unconstrained reaching law, the
within-layer contraction coefficient is `1 − T K/(LCφ) = 0.55`. A positive surface
requires increased voltage. A wider boundary layer prevents excessive sampled feedback.

Parameter mismatch, disturbance variation within a step, sampling delay and actuator
limits affect tracking. No saturated, delayed, nonlinear-load stability theorem is claimed.

## Adaptive-gain SMC

The same surface and equivalent control are used, with a bounded gain:

$$\dot K=\gamma\max(|s|/\phi-\delta,0)-\ell(K-K_{min}).$$

Forward Euler updates `K`, followed by projection onto `[6,25] V`. The initial gain is
`6 V`, growth is `450 V/s` per normalized surface excess, leakage is `8 s⁻¹`, and the
dead zone is `0.15`. Exported diagnostics include the gain range. The corresponding nominal
within-layer contraction coefficient remains between 0.375 and 0.85 at 20 kHz.

This is a pragmatic adaptive switching-gain law. It adapts the robustness term, not L or C.
Gain leakage helps it relax after disturbances. Larger adaptive gains can increase noise
sensitivity; adaptation does not guarantee a better ranking than fixed-gain SMC.

## Constrained MPC

The resistive nominal model is discretized exactly under zero-order hold. At time `k`,
`d = i_load − v/R_nom` is held throughout the prediction horizon of **16 steps (0.8 ms)**.
Stacking the predictions gives `X = F x_k + G U + H d`, with `U` in bridge volts.

The target current is `i* = r/R_nom + C r_dot + d`. The stage objective is

$$\sum_{j=1}^{16}\{(v_j-r_j)^2+0.2(i_j-i_j^*)^2
+0.01(u_j-u_{ff,j})^2+0.02(u_j-u_{j-1})^2\}.$$

The first slew term uses the previous bounded requested voltage. Weights operate on the
stated SI-unit quantities; they are not normalized per-unit weights. The feedforward
target is the nominal inverse plant:

$$u_{ff}=(1+r_L/R)r+(L/R+r_LC)\dot r+LC\ddot r+r_Ld.$$

The QP enforces `−0.98 V_dc ≤ u_j ≤ 0.98 V_dc`. Its Hessian is constant and positive
definite due to the input penalty. OSQP caches the factorization, warm starts, and updates
the linear term and bounds every sample. The horizon uses reference preview, available
from the known sinusoid, and assumes the currently measured DC bus persists.

The solver uses `eps_abs = eps_rel = 1e-5`, at most 1000 iterations, and fixed rho updates
(`adaptive_rho=False`) to avoid time-dependent adaptation. Only a `solved` status with
finite values is accepted. Other statuses activate bounded current feedback, counted as
`solver_fallbacks`. Tests compare the first move with an independently solved bounded QP.

This is continuous-control-set MPC with duty bounds. There is no hard current constraint,
terminal invariant set, terminal Lyapunov cost, nonlinear prediction, or explicit delay
compensation. Peak current and delayed-case behavior are reported to make those limits visible.

See the [OSQP Python interface](https://osqp.org/docs/interfaces/python.html) and
[solver paper](https://arxiv.org/abs/1711.08013) for the numerical solver, distinct from
the controller design choices documented here.
