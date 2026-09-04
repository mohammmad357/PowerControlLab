# Research directions

The current release is a complete simulation benchmark. These are extensions, not
implemented features:

- Calibrate L, C and loss parameters from measured data; validate on held-out experiments.
- Add dead time, switch losses, thermal states and ADC quantization with independent tests.
- Add hard/soft current constraints, terminal ingredients and delay-aware MPC prediction.
- Compare against proportional-resonant control and independently tuned controller families.
- Perform Monte Carlo uncertainty sweeps with confidence intervals and explicit tuning budgets.
- Build hardware-in-the-loop and measured waveform import before claiming a calibrated twin.
- Evaluate learned residual models only against held-out data and physics-only baselines.

