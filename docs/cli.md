# Command-line recipes

Run from the repository root after the [installation steps](../README.md#quick-start).
Inspect available arguments with `python main.py --help`.

## Start with one experiment

```sh
python main.py --controller smc --scenario nominal --mode averaged --seed 7 --output results/cli-nominal
```

Then compare all four controllers with the same scenario:

```sh
python main.py --controller all --scenario load-step --mode averaged --seed 7 --output results/cli-load-step
```

These are reproduction instructions, not a claim that a new run was performed for this guide.
Use a fresh output directory when changing seed, plant parameters or mode.

## Common options

| Option | Default | Purpose |
|---|---|---|
| `--controller` | `smc` | Choose `pi`, `smc`, `adaptive-smc`, `mpc`, or `all` |
| `--scenario` | `nominal` | Choose a named [scenario](benchmark.md#scenarios), or `all` |
| `--mode` | `averaged` | Choose averaged or switching plant integration |
| `--duration` | `0.24` | Simulation duration in seconds |
| `--substeps` | `10` | Integration subdivisions per control interval |
| `--seed` | `7` | Reproducible noise seed |
| `--inductance` | `0.002` | Nominal inductance in henry |
| `--capacitance` | `0.00002` | Nominal capacitance in farad |
| `--output` | `results` | Output directory; not automatically unique |

CLI quantities use SI units. For example, 2.5 mH is `--inductance 0.0025`,
and 25 microfarads is `--capacitance 0.000025`.

## Find the outputs

For the load-step comparison above:

```text
results/cli-load-step/
  benchmark.csv
  benchmark.json
  comparison.png
  load-step/
    smc/
      metrics.json
      run.json
      waveforms.npz
      traces.png
    ...other controllers...
```

`comparison.png` is produced for multiple cases when plots are enabled.
Per-run `run.json` includes configuration, controller parameters and provenance;
keep it with the metrics. The top-level benchmark files summarize this invocation,
not an accumulated history of previous invocations.

## Compact metric-only run

```sh
python main.py --controller smc --scenario nominal --seed 7 --no-plots --no-raw --output results/cli-metrics-only
```

This omits plots and raw arrays for the new run; metrics and configuration are still
saved. These flags do not remove old files from a reused directory, so stale plots
must not be mistaken for outputs of the latest invocation.

See the [metric definitions and limitations](benchmark.md).
