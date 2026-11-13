import csv
import json

from powercontrollab.reporting import save_table


def test_benchmark_exports_preserve_rows_units_and_missing_values(tmp_path):
    rows = [
        {"controller": "pi", "scenario": "nominal", "steady_rmse_v": 1.25, "thd_percent": None},
        {
            "controller": "smc",
            "scenario": 'custom, quoted "case"',
            "steady_rmse_v": 0.5,
            "thd_percent": 2.75,
        },
    ]
    save_table(rows, tmp_path / "benchmark")
    output = tmp_path / "benchmark"
    assert json.loads((output / "benchmark.json").read_text(encoding="utf-8")) == rows
    with (output / "benchmark.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == list(rows[0])
        restored = list(reader)
    assert len(restored) == 2
    assert restored[0]["thd_percent"] == ""
    assert restored[1]["scenario"] == rows[1]["scenario"]
    assert float(restored[0]["steady_rmse_v"]) == 1.25
    assert float(restored[1]["thd_percent"]) == 2.75
