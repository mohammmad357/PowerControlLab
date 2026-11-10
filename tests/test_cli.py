import json

import pytest

from powercontrollab.cli import main


def test_cli_exports_portable_provenance_and_results(tmp_path, capsys):
    main(["--controller", "smc", "--output", str(tmp_path), "--no-plots", "--no-raw"])
    output = capsys.readouterr().out
    assert "SMC" in output and "Saved results" in output
    run = json.loads((tmp_path / "nominal/smc/run.json").read_text())
    assert run["plant"]["dc_voltage"] == 400
    assert len(run["provenance"]["source_sha256"]) == 64
    assert (tmp_path / "benchmark.csv").is_file()


def test_invalid_cli_is_nonzero(tmp_path):
    with pytest.raises(SystemExit) as raised:
        main(["--dc-voltage", "50", "--output", str(tmp_path)])
    assert raised.value.code == 2


def test_invalid_analysis_window_does_not_create_output(tmp_path, capsys):
    destination = tmp_path / "rejected-run"
    with pytest.raises(SystemExit) as raised:
        main(
            [
                "--duration",
                "0.04",
                "--output",
                str(destination),
                "--no-plots",
                "--no-raw",
            ]
        )
    assert raised.value.code == 2
    assert "analysis needs a full cycle" in capsys.readouterr().err
    assert not destination.exists()
