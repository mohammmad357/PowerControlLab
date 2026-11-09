# Reading exported metric fields

This guide describes [`compute_metrics`](../src/powercontrollab/analysis/metrics.py).
Use it alongside the [formal benchmark definitions](benchmark.md), not as a
replacement for the configuration and provenance in `run.json`.

| Field | Units | Interpretation |
|---|---|---|
| `steady_rmse_v` | V | Tracking error over the final analysis cycles |
| `full_run_rmse_v` | V | Tracking error over the run, including startup |
| `output_rms_v` | V | RMS of the output in the final analysis window |
| `fundamental_rms_v` | V | Fundamental component only; not total RMS |
| `dc_offset_v` | V | DC component of the analyzed waveform |
| `thd_percent` | % | Harmonics 2–40 relative to the fundamental |
| `broadband_residual_rms_v` | V | Residual after subtracting the fundamental; can include switching ripple |
| `peak_inductor_current_a` | A | Maximum absolute current across the run |
| `settling_time_s` | s | Recovery relative to `settling_origin_s`, or JSON null |
| `settling_threshold_v` | V | Allowed cycle-RMS error band, 2% of requested RMS voltage |
| `saturation_fraction` | fraction | Fraction at the modulation limit; multiply by 100 for percent |

## Avoid three misleading comparisons

1. The CLI displays settling time in **milliseconds**, but the JSON field is in
   **seconds**. A JSON value of 0.02 s corresponds to 20 ms, not 0.02 ms.
2. JSON `null` for settling means the criterion was not established within the
   finite run. It is neither zero recovery time nor proof of permanent instability.
   Undefined THD is also not zero distortion.
3. Steady and full-run RMSE use different windows. Compare the same field under
   matching configurations rather than selecting whichever number is smaller.

`analysis_start_s` and `analysis_end_s` describe the analysis interval. The final
endpoint sample is excluded from the periodic analysis window to avoid duplicating
both ends. Preserve that convention when independently recomputing metrics.

Identity fields include controller, scenario, mode, effective load and seed.
The effective `load` matters even when the scenario name is `nominal`; see
[load selection](cli.md#load-selection-and-output-paths). Host-dependent compute
diagnostics are not a guarantee that a real-time deadline can be met.
