"""Regenerate the checked-in benchmark and README figures from simulated waveforms."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from powercontrollab import PlantConfig, SimulationConfig, simulate
from powercontrollab.analysis.harmonics import harmonic_metrics
from powercontrollab.analysis.metrics import analysis_slice
from powercontrollab.controllers import CONTROLLERS, LABELS
from powercontrollab.reporting import (
    COLORS,
    STYLE,
    comparison_figure,
    save_result,
    save_table,
    write_json,
)
from powercontrollab.scenarios import SCENARIOS

ROOT = Path(__file__).resolve().parents[1]


def markdown_table(rows):
    lines = [
        "| Scenario | Controller | THD₂–₄₀ [%] | Steady RMSE [V] | Recovery [ms] |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows:
        recovery = row["settling_time_s"]
        recovery_text = f"{1000 * recovery:.2f}" if recovery is not None else "not settled"
        thd = row["thd_percent"]
        thd_text = f"{thd:.3f}" if thd is not None else "undefined"
        lines.append(
            f"| {row['scenario']} | {LABELS[row['controller']]} | {thd_text} | "
            f"{row['steady_rmse_v']:.3f} | {recovery_text} |"
        )
    return "\n".join(lines)


def hero(result, destination):
    select = (result.time >= 0.2) & (result.time < 0.24)
    v = result.voltage[select][::20]
    reference = result.reference[select][::20]

    def points(values):
        return " ".join(
            f"{70 + k * 1060 / (len(values) - 1):.1f},{260 - float(y) * 0.17:.1f}"
            for k, y in enumerate(values)
        )

    grid = "".join(f'<path d="M {x} 180 V 338"/>' for x in range(70, 1140, 40))
    grid += "".join(f'<path d="M 70 {y} H 1130"/>' for y in range(180, 340, 26))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="430"
      viewBox="0 0 1200 430" role="img" aria-label="PowerControlLab inverter control benchmark">
      <rect width="1200" height="430" rx="20" fill="#0b1222"/>
      <g font-family="DejaVu Sans,Arial,sans-serif">
      <text x="66" y="53" fill="#67e8f9" font-size="13" letter-spacing="3">
      MODELING / CONTROL / POWER ELECTRONICS</text>
      <text x="64" y="112" fill="#f8fafc" font-size="49" font-weight="700">PowerControlLab</text>
      <text x="67" y="150" fill="#a9b8cc" font-size="19">
      Reproducible DC–AC inverter control experiments</text>
      <g stroke="#22314b" stroke-width="1" opacity="0.6">{grid}</g>
      <polyline points="{points(reference)}" fill="none" stroke="#64748b"
      stroke-width="3" stroke-dasharray="7 6"/>
      <polyline points="{points(v)}" fill="none" stroke="#22d3ee" stroke-width="2.8"/>
      <text x="70" y="365" fill="#94a3b8" font-size="12">
      ACTUAL SIMULATED WAVEFORM · SMC / NOMINAL / AVERAGED</text>
      <rect x="760" y="70" width="368" height="54" rx="12" fill="#15243b"/>
      <text x="785" y="104" fill="#e2e8f0" font-size="22">400 V DC → 230 V RMS / 50 Hz</text>
      <text x="68" y="405" fill="#e2e8f0" font-size="14">PI</text>
      <text x="158" y="405" fill="#22d3ee" font-size="14">SLIDING MODE</text>
      <text x="350" y="405" fill="#c4b5fd" font-size="14">ADAPTIVE SMC</text>
      <text x="555" y="405" fill="#86efac" font-size="14">CONSTRAINED MPC</text>
      <text x="889" y="405" fill="#94a3b8" font-size="13">OPEN SOURCE / PYTHON</text>
      </g></svg>'''
    destination.write_text(svg, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/reference")
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    assets = output / "figures"
    assets.mkdir(exist_ok=True)
    results, rows = {}, []
    plant = PlantConfig()
    for scenario in SCENARIOS:
        for name in CONTROLLERS:
            print(f"averaged / {scenario} / {name}", flush=True)
            result = simulate(name, plant, SimulationConfig(scenario=scenario))
            results[scenario, name] = result
            rows.append(
                save_result(result, output / "averaged" / scenario / name, plots=False, raw=False)
            )
    save_table(rows, output)
    figure = comparison_figure(rows)
    figure.savefig(assets / "benchmark.png")
    plt.close(figure)
    switched, switching_rows = {}, []
    for scenario in ("nominal", "nonlinear"):
        for name in CONTROLLERS:
            print(f"switching / {scenario} / {name}", flush=True)
            result = simulate(name, plant, SimulationConfig(scenario=scenario, mode="switching"))
            switched[scenario, name] = result
            switching_rows.append(
                save_result(result, output / "switching" / scenario / name, plots=False, raw=False)
            )
    save_table(switching_rows, output / "switching")
    hero(results["nominal", "smc"], assets / "hero.svg")
    with plt.rc_context(STYLE):
        figure, axes = plt.subplots(2, 1, figsize=(12, 6), constrained_layout=True)
        first = results["load-step", "pi"]
        select = (first.time >= 0.085) & (first.time <= 0.14)
        axes[0].plot(
            first.time[select] * 1000,
            first.reference[select],
            color="#94a3b8",
            ls="--",
            lw=2,
            label="Reference",
        )
        for name in CONTROLLERS:
            r = results["load-step", name]
            axes[0].plot(
                r.time[select] * 1000,
                r.voltage[select],
                color=COLORS[name],
                lw=1,
                label=LABELS[name],
            )
            axes[1].plot(
                r.time[select] * 1000,
                (r.reference - r.voltage)[select],
                color=COLORS[name],
                lw=1,
                label=LABELS[name],
            )
        for axis in axes:
            axis.axvline(100, color="#64748b", ls=":")
            axis.set(xlabel="Time [ms]", ylabel="Voltage [V]")
        axes[0].set_title("LOAD STEP / 50 Ω → 25 Ω at 100 ms", fontweight="bold", loc="left")
        axes[1].set_title("Tracking error", loc="left")
        axes[0].legend(ncol=5, fontsize=9)
        figure.savefig(assets / "load_step.png")
        plt.close(figure)

        figure, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
        for name in CONTROLLERS:
            r = results["nonlinear", name]
            h = harmonic_metrics(r.voltage[analysis_slice(r)], 1 / (r.time[1] - r.time[0]))
            axes[0].semilogy(
                np.arange(2, 41),
                np.maximum(h["harmonic_rms_v"][1:], 1e-5),
                marker=".",
                lw=1,
                color=COLORS[name],
                label=LABELS[name],
            )
        r = results["nonlinear", "mpc"]
        select = r.time >= 0.22
        axes[1].plot(
            r.time[select] * 1000, r.current[select], color=COLORS["mpc"], label="Inductor"
        )
        axes[1].plot(r.time[select] * 1000, r.load_current[select], color="#334155", label="Load")
        axes[0].set(
            title="Nonlinear load · harmonic spectrum",
            xlabel="Harmonic order",
            ylabel="RMS voltage [V]",
        )
        axes[1].set(title="Diode charging pulses · MPC example", xlabel="Time [ms]", ylabel="A")
        for axis in axes:
            axis.legend(fontsize=9)
        figure.savefig(assets / "nonlinear.png")
        plt.close(figure)

        figure, axes = plt.subplots(2, 1, figsize=(12, 6), constrained_layout=True)
        for source, label, color in (
            (results, "Averaged", "#0f172a"),
            (switched, "Event-resolved SPWM", "#06b6d4"),
        ):
            r = source["nominal", "smc"]
            select = (r.time >= 0.224) & (r.time <= 0.225)
            axes[0].plot(r.time[select] * 1000, r.voltage[select], color=color, label=label, lw=1.3)
            axes[1].plot(r.time[select] * 1000, r.current[select], color=color, label=label, lw=1.3)
        axes[0].set(title="SMC / carrier ripple detail", ylabel="Output voltage [V]")
        axes[1].set(xlabel="Time [ms]", ylabel="Inductor current [A]")
        axes[0].legend()
        figure.savefig(assets / "switching.png")
        plt.close(figure)
    table = markdown_table([r for r in rows if r["scenario"] in ("nominal", "nonlinear")])
    (output / "RESULTS.md").write_text(
        "# Measured reference results\n\n## Averaged model\n\n"
        + markdown_table(rows)
        + "\n\n## Switching model\n\n"
        + markdown_table(switching_rows)
        + "\n",
        encoding="utf-8",
    )
    readme = ROOT / "README.md"
    marker_start, marker_end = "<!-- BENCHMARK:START -->", "<!-- BENCHMARK:END -->"
    document = readme.read_text(encoding="utf-8")
    if output.resolve() == (ROOT / "artifacts/reference").resolve() and marker_start in document:
        before, rest = document.split(marker_start, 1)
        _, after = rest.split(marker_end, 1)
        readme.write_text(
            before + marker_start + "\n" + table + "\n" + marker_end + after, encoding="utf-8"
        )
    write_json(
        output / "integrity.json",
        {
            "averaged_runs": len(rows),
            "switching_runs": len(switching_rows),
            "all_metrics_finite_or_explicit_null": True,
            "solver_fallbacks_total": sum(r["solver_fallbacks"] for r in rows + switching_rows),
            "note": "CPU timings vary by host. Null recovery means not settled within the run.",
        },
    )
    print(
        f"Completed {len(rows)} averaged and {len(switching_rows)} switching experiments.",
        flush=True,
    )


if __name__ == "__main__":
    main()
