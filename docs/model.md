# Plant and numerical model

PowerControlLab models a **standalone voltage-source inverter**, not a grid-connected
current-source converter. The topology is DC bus → ideal H-bridge → lossy L → shunt C → load.
All internal quantities use SI units.

## States and equations

Let `i` be the filter-inductor current, `v` the output voltage, `u` the bridge voltage,
and `i_load` the load current. Kirchhoff's laws give

$$L\dot i=u-v-r_Li,\qquad C\dot v=i-i_{load}.$$

For a resistive load, `i_load = v/R`. With `x = [i, v]ᵀ`,

$$A=\begin{bmatrix}-r_L/L&-1/L\\1/C&-1/(RC)\end{bmatrix},\quad
B_u=\begin{bmatrix}1/L\\0\end{bmatrix},\quad
B_d=\begin{bmatrix}0\\-1/C\end{bmatrix}.$$

The MPC model uses `i_load = v/R_nom + d`, with measured residual `d` held constant
over each prediction horizon. It never receives the plant's actual L, C, future disturbance
schedule, or rectifier capacitor state.

## Default operating point

| Quantity | Value |
|---|---:|
| DC source | 400 V |
| Reference | 230 Vrms, 50 Hz |
| L / C | 2 mH / 20 µF |
| Inductor series resistance | 0.15 Ω |
| Resistive load | 50 Ω (about 1.06 kW at nominal voltage) |
| Controller and carrier frequency | 20 kHz |
| Modulation limit | ±0.98 |
| Integration step | 5 µs (10 substeps per control interval) |
| Simulation / soft start | 240 ms / 20 ms |

These are study parameters, not a reproduction of a commercial board. The unloaded LC
resonance is approximately 796 Hz. The nominal reference peak is about 325 V, giving
modulation headroom at 400 V. During the default 10% DC sag, the actuator limit is 352.8 V.

## Dynamic nonlinear load

The nonlinear case adds a diode bridge, series resistance `R_s`, and a parallel DC
capacitor/resistor to the existing AC resistor. Its third state is `v_d`, initially zero:

$$i_d=\max\left(\frac{|v|-v_d-2V_D}{R_s},0\right),\qquad
C_d\dot v_d=i_d-\frac{v_d}{R_d},$$

$$i_{load}=\frac vR+\operatorname{sign}(v)i_d.$$

Defaults are `R_s = 3 Ω`, `C_d = 470 µF`, `R_d = 100 Ω`, and `V_D = 0.7 V` per diode.
This produces capacitor charging pulses and an initial charging transient. It is a
piecewise-smooth circuit model with finite source resistance; diode recovery and junction
capacitance are omitted. The load remains passive. An independent test checks the complete
instantaneous energy balance, including diode, source-resistor and DC-load dissipation.

## Averaged and switched plants

In averaged mode, `u = m V_dc` during one control interval. This resolves the control and
load dynamics but cannot reproduce carrier ripple, switching losses, or dead time.

In switching mode, the two bridge legs compare `m` and `-m` against the same triangular
carrier `c(φ) = 4|φ − 1/2| − 1`, where `0 ≤ φ < 1`. Thus

$$u=V_{dc}\{\mathbf{1}[m\ge c]-\mathbf{1}[-m\ge c]\}\in\{-V_{dc},0,V_{dc}\}.$$

The carrier runs at 20 kHz; unipolar bridge ripple also has components at twice that frequency.
The integrator splits each fixed recording interval at **exact PWM transition times**.
Duty ratio is not rounded to a small number of integration bins. Tests verify that the
period-average bridge voltage equals `m V_dc`, including very short pulses.

Classical fourth-order Runge–Kutta advances the electrical states. Resistive-load trajectories
are checked against an independent matrix exponential. A nonlinear load refinement test
checks convergence when the integration step is halved. The script
`python scripts/validate_numerics.py` records both averaged and switched convergence evidence.

The exported `bridge_voltage` is the **mean voltage over the following recording bin**;
state samples are instantaneous at the bin boundaries. This distinction matters near
switching transitions. The final command and bridge samples repeat the preceding values
for plotting; metric windows exclude that final endpoint.

## Causality and sensing

At each sample the controller reads noisy `v`, `i`, and `i_load`, plus the ideal measured DC
bus. It computes a bridge-voltage request, which is limited to the common duty bound.
Optional delay is a FIFO of **modulation commands**: a queued command uses the DC bus that
exists when it is applied. Parameters and DC/load steps are constant within each control
interval. Events must align with the controller clock.

All controllers share the same measurements. Noise draws are generated from the same seed
and sample schedule. Metrics use true simulated states, not noise-corrupted observations.

## Digital-twin scope

This release is a **simulation-based digital-twin foundation**. It has no live hardware
connection, parameter-identification pipeline, sensor calibration, thermal model, magnetic
saturation, switch loss model, dead time, grid synchronization, or hardware protection logic.
The software tests verify its equations and numerical implementation; they do not validate
a physical inverter. There is no claim of real-time execution, standards certification,
global closed-loop stability, or controller superiority outside the reported experiments.

For physical topology context, see TI's [single-phase inverter reference design](https://www.ti.com/tool/TIDM-HV-1PH-DCAC).
Its voltage-source mode also uses an LC output filter; our parameters and controller laws
are independently chosen. Exact ZOH prediction uses SciPy's
[documented discretization interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.cont2discrete.html).

