"""The `run` and `baseline` commands end to end, with a fake LLM (no API calls)."""

import json

import pytest

from discovery_chef import cli, runs
from discovery_chef.llm import LLMConfig, RunTracker
from discovery_chef.llm.pricing import TokenUsage
from tests.test_orchestrator import FakeLLM, critique


@pytest.fixture
def offline(monkeypatch, tmp_path, passing_brief):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(runs, "RUNS_DIR", tmp_path)
    tracker = RunTracker()
    tracker.add_call(agent="brief_writer", step="draft", latency_s=2.0, finish_reason="STOP",
                     usage=TokenUsage("gemini-3.8-flash", 1000, 500))
    llm = FakeLLM(passing_brief, [critique("approve")])
    monkeypatch.setattr(cli, "_llm", lambda args: (llm, LLMConfig(), tracker))
    return tmp_path


def test_run_writes_a_complete_run_folder(offline, capsys):
    assert cli.main(["run"]) == 0
    (run_dir,) = offline.iterdir()
    for name in ("config.json", "brief.md", "brief.json", "citation_check.json", "review.md",
                 "usage.json", "run.json", "agents/research_synthesis.json"):
        assert (run_dir / name).exists(), name
    run = json.loads((run_dir / "run.json").read_text())
    assert run["loop_outcome"] == "approved"
    assert run["totals"]["cost_usd"] == pytest.approx((1000 * 0.75 + 500 * 3.75) / 1e6)
    assert "recommendation     test_further" in capsys.readouterr().out


def test_baseline_writes_a_run_folder(offline):
    assert cli.main(["baseline", "--variant", "informed"]) == 0
    (run_dir,) = offline.iterdir()
    assert run_dir.name.endswith("baseline-informed")
    run = json.loads((run_dir / "run.json").read_text())
    assert run["final_citation_check"]["passed"] is True


def test_missing_credentials_fail_before_creating_a_run(monkeypatch, tmp_path):
    for name in cli.CREDENTIAL_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(cli, "ENV_FILE", tmp_path / "missing.env")
    monkeypatch.setattr(runs, "RUNS_DIR", tmp_path / "runs")
    assert cli.main(["run"]) == 2
    assert not (tmp_path / "runs").exists()
