import json

import pytest

from powercontrollab.reporting import write_json


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_json_does_not_overwrite_existing_report(tmp_path, invalid):
    path = tmp_path / "metrics.json"
    original = '{"settling_time_s": null}\n'
    path.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError):
        write_json(path, {"metric": invalid})
    assert path.read_text(encoding="utf-8") == original


def test_missing_metric_round_trips_as_json_null(tmp_path):
    path = tmp_path / "metrics.json"
    write_json(path, {"settling_time_s": None, "steady_rmse_v": 1.25})
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "settling_time_s": None,
        "steady_rmse_v": 1.25,
    }
