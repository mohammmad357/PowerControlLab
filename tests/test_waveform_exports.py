import json
from dataclasses import asdict

import numpy as np

from powercontrollab import SimulationConfig, simulate
from powercontrollab.reporting import save_result


def test_waveform_archive_matches_simulated_state_and_run_metadata(tmp_path):
    config = SimulationConfig(duration=0.08, analysis_cycles=1)
    result = simulate("pi", config=config)
    metrics = save_result(result, tmp_path, plots=False, raw=True)
    with np.load(tmp_path / "waveforms.npz", allow_pickle=False) as archive:
        expected = result.arrays()
        assert set(archive.files) == set(expected)
        for name, values in expected.items():
            np.testing.assert_array_equal(archive[name], values)
            assert archive[name].shape == result.time.shape
    run = json.loads((tmp_path / "run.json").read_text(encoding="utf-8"))
    assert run["simulation"] == asdict(config)
    assert run["plant"] == asdict(result.plant)
    assert run["controller"] == "pi"
    assert json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8")) == metrics
    assert not (tmp_path / "traces.png").exists()
