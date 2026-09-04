from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


def test_dashboard_runs_and_displays_computed_metrics():
    path = Path(__file__).parents[1] / "dashboard/app.py"
    app = AppTest.from_file(str(path), default_timeout=60).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert len(app.dataframe) == 1
    assert "thd_percent" in app.dataframe[0].value.columns
