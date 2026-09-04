import numpy as np
import pytest

from powercontrollab.analysis.harmonics import harmonic_metrics, rms_spectrum
from powercontrollab.analysis.metrics import settling_time


def test_known_harmonics_dc_offset_and_parseval():
    fs = 20_000
    t = np.arange(2000) / fs
    signal = 3 + np.sqrt(2) * (
        230 * np.sin(2 * np.pi * 50 * t)
        + 6.9 * np.sin(2 * np.pi * 150 * t)
        + 9.2 * np.cos(2 * np.pi * 250 * t)
    )
    result = harmonic_metrics(signal, fs)
    assert result["thd_percent"] == pytest.approx(5, abs=1e-10)
    assert result["fundamental_rms_v"] == pytest.approx(230)
    assert result["dc_offset_v"] == pytest.approx(3)
    _, spectrum = rms_spectrum(signal, fs)
    assert np.sum(spectrum**2) == pytest.approx(np.mean(signal**2))


def test_coherent_pure_sine_and_undefined_zero_fundamental():
    t = np.arange(2000) / 20_000
    assert harmonic_metrics(np.sin(2 * np.pi * 50 * t), 20_000)["thd_percent"] < 1e-10
    assert harmonic_metrics(np.zeros_like(t), 20_000)["thd_percent"] is None


def test_thd_rejects_incoherent_window_and_insufficient_bandwidth():
    with pytest.raises(ValueError, match="integer number"):
        harmonic_metrics(np.ones(2001), 20_000)
    with pytest.raises(ValueError, match="Nyquist"):
        harmonic_metrics(np.ones(400), 4000)


def test_settling_requires_staying_within_band():
    error = np.full(2400, 10.0)
    error[500:] = 0
    settled = settling_time(error, 1e-4, 50, 0, 0.1)
    assert settled == pytest.approx(0.07)
    error[-10:] = 20
    assert settling_time(error, 1e-4, 50, 0, 0.1) is None
