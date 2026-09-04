"""Portable results, configuration provenance and publication-friendly figures."""

import csv
import hashlib
import importlib.metadata
import json
import platform
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .analysis.harmonics import harmonic_metrics
from .analysis.metrics import analysis_slice, compute_metrics
from .controllers import LABELS

COLORS = {"pi": "#fb923c", "smc": "#06b6d4", "adaptive-smc": "#8b5cf6", "mpc": "#22c55e"}
STYLE = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.18,
    "figure.facecolor": "#f8fafc",
    "axes.facecolor": "#ffffff",
    "axes.labelcolor": "#334155",
    "text.color": "#0f172a",
    "savefig.dpi": 170,
}


def provenance():
    root = Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes().replace(b"\r\n", b"\n"))
    versions = {
        name: importlib.metadata.version(name) for name in ("numpy", "scipy", "matplotlib", "osqp")
    }
    from . import __version__

    versions["powercontrollab"] = __version__
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "dependencies": versions,
        "source_sha256": digest.hexdigest(),
    }


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def trace_figure(result):
    p = result.plant
    metrics = compute_metrics(result)
    color = COLORS[result.controller]
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
        last = result.time >= result.time[-1] - 2 / p.frequency
        axes[0, 0].plot(
            result.time[last] * 1e3,
            result.reference[last],
            color="#94a3b8",
            ls="--",
            lw=1.6,
            label="Reference",
        )
        axes[0, 0].plot(
            result.time[last] * 1e3,
            result.voltage[last],
            color=color,
            lw=1,
            label=LABELS[result.controller],
        )
        axes[0, 0].set(title="Output voltage · final two cycles", xlabel="Time [ms]", ylabel="V")
        axes[0, 0].legend(loc="upper right")
        axes[0, 1].plot(result.time * 1e3, result.reference - result.voltage, color=color, lw=0.7)
        axes[0, 1].set(title="Tracking error · complete run", xlabel="Time [ms]", ylabel="V")
        axes[1, 0].plot(result.time * 1e3, result.modulation, color=color, lw=0.8)
        axes[1, 0].set(
            title="Applied modulation", xlabel="Time [ms]", ylabel="m", ylim=(-1.05, 1.05)
        )
        h = harmonic_metrics(
            result.voltage[analysis_slice(result)],
            1 / (result.time[1] - result.time[0]),
            p.frequency,
        )
        amps = np.asarray(h["harmonic_rms_v"])
        axes[1, 1].bar(np.arange(2, 41), amps[1:], color=color)
        thd = metrics["thd_percent"]
        thd_text = f"{thd:.3f}%" if thd is not None else "undefined"
        axes[1, 1].set(
            title=f"Harmonics 2–40 · THD {thd_text}",
            xlabel="Harmonic order",
            ylabel="RMS voltage [V]",
        )
        fig.suptitle(
            f"{LABELS[result.controller]} / {result.config.scenario} / {result.config.mode}"
            f"   |   {p.dc_voltage:g} V DC → {p.voltage_rms:g} Vrms / {p.frequency:g} Hz",
            fontsize=14,
            fontweight="bold",
        )
        return fig


def save_result(result, directory, plots=True, raw=True):
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    metrics = compute_metrics(result)
    write_json(output / "metrics.json", metrics)
    write_json(
        output / "run.json",
        {
            "plant": asdict(result.plant),
            "simulation": asdict(result.config),
            "controller": result.controller,
            "controller_parameters": result.controller_parameters,
            "provenance": provenance(),
        },
    )
    if raw:
        np.savez_compressed(output / "waveforms.npz", **result.arrays())
    if plots:
        figure = trace_figure(result)
        figure.savefig(output / "traces.png")
        plt.close(figure)
    return metrics


def save_table(rows, directory):
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / "benchmark.json", rows)
    with (output / "benchmark.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def comparison_figure(rows):
    controllers = list(dict.fromkeys(row["controller"] for row in rows))
    scenarios = list(dict.fromkeys(row["scenario"] for row in rows))
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(
            1, 2, figsize=(12, max(4, len(scenarios) * 0.56)), constrained_layout=True
        )
        for axis, key, title in zip(
            axes,
            ("steady_rmse_v", "thd_percent"),
            ("Steady-state RMSE [V]", "THD · harmonics 2–40 [%]"),
            strict=True,
        ):
            matrix = np.array(
                [
                    [
                        next(
                            row[key]
                            for row in rows
                            if row["controller"] == c and row["scenario"] == s
                        )
                        for c in controllers
                    ]
                    for s in scenarios
                ],
                dtype=float,
            )
            axis.imshow(np.log10(np.maximum(matrix, 1e-4)), cmap="Blues", aspect="auto")
            for i in range(len(scenarios)):
                for j in range(len(controllers)):
                    axis.text(
                        j,
                        i,
                        f"{matrix[i, j]:.3f}",
                        ha="center",
                        va="center",
                        color="#0f172a" if matrix[i, j] < np.max(matrix) * 0.15 else "white",
                    )
            axis.set_xticks(range(len(controllers)), [LABELS[c] for c in controllers], rotation=18)
            axis.set_yticks(range(len(scenarios)), scenarios)
            axis.set_title(title, fontweight="bold", pad=16)
            axis.grid(False)
        fig.suptitle(
            "POWERCONTROLLAB / fixed gains, common scenarios", fontsize=17, fontweight="bold"
        )
        return fig
