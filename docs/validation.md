# Understanding configuration validation

Invalid configurations are rejected before integration. Use the error text to fix
the experiment rather than disabling validation. This guide follows
[`config.py`](../src/powercontrollab/config.py).

## Voltage headroom

The requested sinusoidal peak must satisfy:

`sqrt(2) * voltage_rms < dc_voltage * modulation_limit`

With the defaults, 230 Vrms requests about 325.27 V peak; the nominal modulation
headroom is 392 V (400 V times 0.98). The inequality is strict.
Passing this nominal check does not guarantee tracking after a DC sag.

## Duration and analysis window

At 50 Hz, duration must be an integer multiple of 20 ms. It must also leave the
final five analysis cycles after startup or the relevant disturbance, with one
additional cycle of separation as checked by `validate_for`.

For default load-step settings, 0.20 s is rejected: the final analysis window
would start at 0.10 s, before the required 0.12 s boundary. A duration of 0.24 s
satisfies that timing check. Changing frequency or API timing parameters changes
these conditions; a duration acceptable for one configuration may fail another.

## Integration resolution

`substeps` must be an integer at least 2. A valid integer can still be too small:
the step must resolve LC dynamics and, for nonlinear loads, diode conduction.
When the error requests more substeps, increase `--substeps` and repeat a
resolution study. Passing the check is not proof of numerical convergence.

## Other constraints

- Plant numeric fields must be finite and positive; modulation limit is in (0, 1].
- The controller/carrier frequency must exceed 80 times the fundamental, and
  their ratio must be an integer within the validation tolerance.
- Seeds and delay samples are nonnegative integers; booleans are rejected as
  substitutes for integer API configuration fields.
- Noise standard deviations may be zero but cannot be negative.
- Disturbance event times must align with controller samples in scenarios that
  use a timed load/DC event, and the event must occur before the run ends.

Some settings are available through the Python API rather than CLI flags. See
[CLI recipes](cli.md) and the [benchmark protocol](benchmark.md). These are
implementation constraints, not a hardware operating envelope or safety certification.
