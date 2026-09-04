"""Command-line runner for individual experiments and complete benchmark matrices."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from .config import PlantConfig, SimulationConfig
from .controllers import CONTROLLERS, LABELS
from .reporting import comparison_figure, save_result, save_table
from .scenarios import SCENARIOS
from .simulation import simulate


def parser():
    result = argparse.ArgumentParser(description="PowerControlLab · DC–AC inverter benchmarks")
    result.add_argument("--controller", choices=[*CONTROLLERS, "all"], default="smc")
    result.add_argument("--scenario", choices=[*SCENARIOS, "all"], default="nominal")
    result.add_argument("--load", choices=["resistive", "nonlinear"], default="resistive")
    result.add_argument("--mode", choices=["averaged", "switching"], default="averaged")
    result.add_argument("--duration", type=float, default=0.24)
    result.add_argument("--dc-voltage", type=float, default=400)
    result.add_argument("--voltage-rms", type=float, default=230)
    result.add_argument("--frequency", type=float, default=50)
    result.add_argument("--resistance", type=float, default=50)
    result.add_argument("--inductance", type=float, default=2e-3, help="Nominal L in henry")
    result.add_argument("--capacitance", type=float, default=20e-6, help="Nominal C in farad")
    result.add_argument("--substeps", type=int, default=10)
    result.add_argument("--seed", type=int, default=7)
    result.add_argument("--output", type=Path, default=Path("results"))
    result.add_argument("--no-plots", action="store_true")
    result.add_argument("--no-raw", action="store_true")
    return result


def main(argv=None):
    plt.switch_backend("Agg")
    arguments = parser()
    args = arguments.parse_args(argv)
    try:
        plant = PlantConfig(
            dc_voltage=args.dc_voltage,
            voltage_rms=args.voltage_rms,
            frequency=args.frequency,
            load_resistance=args.resistance,
            inductance=args.inductance,
            capacitance=args.capacitance,
        )
        controllers = list(CONTROLLERS) if args.controller == "all" else [args.controller]
        scenarios = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
        print(
            f"PowerControlLab | {plant.dc_voltage:g} V DC -> {plant.voltage_rms:g} Vrms / "
            f"{plant.frequency:g} Hz | {args.mode} | fs={plant.switching_frequency:g} Hz"
        )
        print(f"{'Scenario':<12} {'Controller':<14} {'THD %':>9} {'RMSE V':>9} {'Settling ms':>12}")
        rows = []
        for scenario in scenarios:
            config = SimulationConfig(
                duration=args.duration,
                scenario=scenario,
                load=args.load,
                mode=args.mode,
                substeps=args.substeps,
                seed=args.seed,
            )
            config.validate_for(plant)
            for controller in controllers:
                result = simulate(controller, plant, config)
                output = args.output / scenario / controller
                metrics = save_result(result, output, plots=not args.no_plots, raw=not args.no_raw)
                rows.append(metrics)
                settling = metrics["settling_time_s"]
                settled = f"{settling * 1000:.2f}" if settling is not None else "not settled"
                thd = metrics["thd_percent"]
                thd_text = f"{thd:.3f}" if thd is not None else "undefined"
                print(
                    f"{scenario:<12} {LABELS[controller]:<14} {thd_text:>9} "
                    f"{metrics['steady_rmse_v']:>9.3f} {settled:>12}",
                    flush=True,
                )
        save_table(rows, args.output)
        if len(rows) > 1 and not args.no_plots:
            figure = comparison_figure(rows)
            figure.savefig(args.output / "comparison.png")
            plt.close(figure)
        print(f"Saved results to {args.output.resolve()}")
    except (ValueError, RuntimeError) as error:
        arguments.error(str(error))


if __name__ == "__main__":
    main()
