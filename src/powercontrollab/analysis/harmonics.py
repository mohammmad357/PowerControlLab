"""Single-sided RMS spectrum and coherent-bin THD; no window or hidden resampling."""

import numpy as np


def rms_spectrum(signal, sample_rate):
    values = np.asarray(signal, dtype=float)
    if values.ndim != 1 or values.size < 4 or not np.all(np.isfinite(values)):
        raise ValueError("signal must be a finite 1D array with at least four samples")
    if not np.isfinite(sample_rate) or sample_rate <= 0:
        raise ValueError("sample_rate must be positive and finite")
    amplitudes = np.abs(np.fft.rfft(values)) / values.size
    amplitudes[1:] *= np.sqrt(2)
    if values.size % 2 == 0:
        amplitudes[-1] /= np.sqrt(2)
    return np.fft.rfftfreq(values.size, 1 / sample_rate), amplitudes


def harmonic_metrics(signal, sample_rate, fundamental=50.0, maximum_harmonic=40):
    frequency, spectrum = rms_spectrum(signal, sample_rate)
    if not np.isfinite(fundamental) or fundamental <= 0:
        raise ValueError("fundamental must be finite and positive")
    if not isinstance(maximum_harmonic, int) or maximum_harmonic < 2:
        raise ValueError("maximum_harmonic must be an integer >= 2")
    bin_float = len(signal) * fundamental / sample_rate
    fundamental_bin = round(bin_float)
    if fundamental_bin < 1 or not np.isclose(bin_float, fundamental_bin, atol=1e-8, rtol=0):
        raise ValueError("THD requires an integer number of fundamental cycles")
    # Keep requested harmonics strictly below Nyquist (no silent truncation).
    if maximum_harmonic * fundamental >= sample_rate / 2:
        raise ValueError("Requested harmonic bandwidth must be below Nyquist")
    indices = fundamental_bin * np.arange(1, maximum_harmonic + 1)
    harmonics = spectrum[indices]
    v1 = float(harmonics[0])
    thd = float(100 * np.linalg.norm(harmonics[1:]) / v1) if v1 > 1e-10 else None
    all_ac_power = float(np.sum(spectrum[1:] ** 2))
    broadband = float(np.sqrt(max(0, all_ac_power - v1 * v1)))
    return {
        "thd_percent": thd,
        "fundamental_rms_v": v1,
        "dc_offset_v": float(np.mean(signal)),
        "broadband_residual_rms_v": broadband,
        "harmonic_rms_v": harmonics.tolist(),
        "harmonic_frequencies_hz": frequency[indices].tolist(),
    }
