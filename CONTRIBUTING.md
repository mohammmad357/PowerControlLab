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

