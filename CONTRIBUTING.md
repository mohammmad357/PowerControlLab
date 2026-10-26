# Contributing

Install `python -m pip install -e ".[dev,dashboard]"`, then run `python -m pytest`,
`python -m ruff check .` and `python -m ruff format --check .` before opening a PR.

Use SI units in model code and include equations or a primary reference for physical changes.
Keep controller parameters fixed across scenarios. Do not change published numbers by hand:
run `python scripts/reproduce.py` after changes that affect simulation behavior.

A new controller needs a fresh-state factory entry, the common `Measurement` interface,
explicit actuator handling, a nominal closed-loop test and a documented mathematical law.
A new plant model needs an independent analytical limit or convergence test.

Report software bugs with the exact command, seed, `run.json` and the observed result.
Discuss model assumptions and controller tuning in issues; negative benchmark results are useful.


## Minimal reproducible bug report

Copy this checklist into an issue and replace the example values with the actual run:

```text
Commit or release:
Python version and operating system:
Exact command (run from the repository root):
Controller / scenario / mode / seed:
Expected behavior:
Actual behavior and complete error message:
Smallest configuration that still reproduces the problem:
```

Attach the affected run's `run.json` and `metrics.json` when available. If the run
failed before creating them, include the command and traceback instead; missing
artifacts should not prevent reporting a startup failure. Keep measured timings
separate from correctness and physical-validation claims. Remove credentials,
private paths and unrelated personal information from shared diagnostics.
