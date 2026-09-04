"""Metrics on true output states, not the noisy measurements used by controllers."""

import numpy as np

from .harmonics import harmonic_metrics


def cycle_rms_error(error, samples_per_cycle):
    """Trailing full-cycle RMS, timestamped at the right-hand boundary of each window."""
    squared = np.asarray(error, dtype=float) ** 2
    cumulative = np.concatenate(([0.0], np.cumsum(squared)))
    return np.sqrt(
        np.maximum(
            0,
            (cumulative[samples_per_cycle:] - cumulative[:-samples_per_cycle]) / samples_per_cycle,
        )
    )


def settling_time(error, dt, frequency, origin, threshold):
    n = round(1 / (dt * frequency))
    rolling = cycle_rms_error(error, n)
    times = np.arange(n, len(error) + 1) * dt
    eligible = times >= origin + 1 / frequency - 1e-10
    within = rolling <= threshold
    stays_within = np.logical_and.accumulate(within[::-1])[::-1]
    # Require one additional complete cycle of observation after first qualifying window.
    eligible &= times <= len(error) * dt - 1 / frequency + 1e-10
    indices = np.flatnonzero(eligible & stays_within)
    return float(times[indices[0]] - origin) if indices.size else None


def analysis_slice(result):
    samples_per_cycle = round(1 / (result.plant.frequency * (result.time[1] - result.time[0])))
    count = result.config.analysis_cycles * samples_per_cycle
    # Drop endpoint: including both ends of a periodic window creates spectral leakage.
    return slice(len(result.time) - 1 - count, len(result.time) - 1)


def compute_metrics(result):
    p, cfg = result.plant, result.config
    dt = result.time[1] - result.time[0]
    steady = analysis_slice(result)
    voltage = result.voltage[steady]
    error = result.reference - result.voltage
    harmonics = harmonic_metrics(voltage, 1 / dt, p.frequency)
    origin = (
        cfg.event_time if cfg.scenario in ("load-step", "dc-sag", "combined") else cfg.ramp_time
    )
    settled = settling_time(error[:-1], dt, p.frequency, origin, 0.02 * p.voltage_rms)
    return {
        "controller": result.controller,
        "scenario": cfg.scenario,
        "mode": cfg.mode,
        "load": result.diagnostics["effective_load"],
        "seed": cfg.seed,
        "thd_percent": harmonics["thd_percent"],
        "steady_rmse_v": float(np.sqrt(np.mean(error[steady] ** 2))),
        "full_run_rmse_v": float(np.sqrt(np.mean(error[:-1] ** 2))),
        "output_rms_v": float(np.sqrt(np.mean(voltage**2))),
        "fundamental_rms_v": harmonics["fundamental_rms_v"],
        "dc_offset_v": harmonics["dc_offset_v"],
        "broadband_residual_rms_v": harmonics["broadband_residual_rms_v"],
        "peak_inductor_current_a": float(np.max(np.abs(result.current))),
        "settling_time_s": settled,
        "settling_origin_s": origin,
        "settling_threshold_v": 0.02 * p.voltage_rms,
        "analysis_start_s": float(result.time[steady.start]),
        "analysis_end_s": float(result.time[-1]),
        "maximum_harmonic": 40,
        "saturation_fraction": float(
            np.mean(
                np.abs(result.commanded_modulation[: -1 : cfg.substeps])
                >= p.modulation_limit - 1e-7
            )
        ),
        **result.diagnostics,
    }
