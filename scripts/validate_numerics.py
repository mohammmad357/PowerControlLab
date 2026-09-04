"""Save integration refinement evidence for the nonlinear plant in both modes."""

from pathlib import Path

import numpy as np

from powercontrollab import SimulationConfig, simulate
from powercontrollab.analysis import compute_metrics
from powercontrollab.reporting import write_json


def main():
    rows = []
    for mode in ("averaged", "switching"):
        results = [
            simulate("mpc", config=SimulationConfig(scenario="nonlinear", mode=mode, substeps=n))
            for n in (10, 20, 40)
        ]
        fine = results[-1]
        for result in results[:-1]:
            factor = fine.config.substeps // result.config.substeps
            difference = result.voltage - fine.voltage[::factor]
            metrics = compute_metrics(result)
            row = {
                "mode": mode,
                "substeps": result.config.substeps,
                "reference_substeps": 40,
                "max_voltage_difference_v": float(np.max(np.abs(difference))),
                "rms_voltage_difference_v": float(np.sqrt(np.mean(difference**2))),
                "thd_percent": metrics["thd_percent"],
                "thd_difference_percentage_points": abs(
                    metrics["thd_percent"] - compute_metrics(fine)["thd_percent"]
                ),
            }
            rows.append(row)
            print(row, flush=True)
    output = Path(__file__).resolve().parents[1] / "artifacts/reference/convergence.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, rows)
    if any(row["max_voltage_difference_v"] > 0.25 for row in rows):
        raise RuntimeError("Refinement exceeds the documented 0.25 V numerical acceptance bound")


if __name__ == "__main__":
    main()
