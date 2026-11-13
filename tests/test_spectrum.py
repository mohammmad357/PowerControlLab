import numpy as np
import pytest

from powercontrollab.analysis.harmonics import rms_spectrum


@pytest.mark.parametrize("count", [1000, 1001])
def test_highest_fft_bin_preserves_rms_energy(count):
    # The last bin is Nyquist only for even-length records.
    sample = np.arange(count)
    last_bin = count // 2
    signal = 3 + 7 * np.cos(2 * np.pi * last_bin * sample / count)
    frequency, spectrum = rms_spectrum(signal, 20_000)
    expected_ac_rms = 7 if count % 2 == 0 else 7 / np.sqrt(2)
    assert spectrum[0] == pytest.approx(3, abs=1e-11)
    assert spectrum[-1] == pytest.approx(expected_ac_rms, abs=1e-11)
    assert frequency[-1] == pytest.approx(last_bin * 20_000 / count)
    assert np.sum(spectrum**2) == pytest.approx(np.mean(signal**2), rel=1e-12)
