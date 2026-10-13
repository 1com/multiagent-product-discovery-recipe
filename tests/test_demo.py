"""The demo app renders every tab on a recorded run, headless (no browser, no API)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from discovery_chef.runs import RUNS_DIR

APP = Path(__file__).parents[1] / "src" / "discovery_chef" / "demo.py"


@pytest.mark.skipif(not any(RUNS_DIR.glob("*-agents/run.json")), reason="no recorded runs")
def test_demo_renders_a_recorded_run():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert [t.label for t in app.tabs] == ["Overview", "Agents", "Critic", "Final brief",
                                           "Comparison"]
    assert app.metric[0].label == "Recommendation"
