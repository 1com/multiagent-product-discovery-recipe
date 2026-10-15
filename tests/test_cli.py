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


def test_baseline_with_critic_records_the_loop(offline):
    assert cli.main(["baseline", "--variant", "informed", "--critic"]) == 0
    (run_dir,) = offline.iterdir()
    assert run_dir.name.endswith("baseline-informed-critic")
    run = json.loads((run_dir / "run.json").read_text())
    assert run["mode"] == "baseline-informed-critic" and run["loop_outcome"] == "approved"
    assert run["config"]["critic"] is True and len(run["rounds"]) == 1
    assert (run_dir / "review.md").exists() and (run_dir / "review" / "round-0").is_dir()


def test_experiment_runs_all_four_systems(offline, monkeypatch, passing_brief):
    llm = FakeLLM(passing_brief, [critique("approve"), critique("approve")])
    monkeypatch.setattr(cli, "_llm", lambda args: (llm, LLMConfig(), RunTracker()))
    assert cli.main(["experiment", "--repeats", "1"]) == 0
    modes = sorted(d.name.split("-", 2)[2] for d in offline.iterdir())
    assert modes == ["agents", "baseline-informed", "baseline-informed-critic",
                     "baseline-naive"]


def test_experiment_stops_when_the_quota_is_exhausted(offline, monkeypatch, capsys):
    from discovery_chef.llm import QuotaExhaustedError

    class QuotaLLM:
        config = LLMConfig()

        def run(self, **kwargs):
            raise QuotaExhaustedError("quota for gemini-3.8-flash exhausted")

    monkeypatch.setattr(cli, "_llm", lambda args: (QuotaLLM(), LLMConfig(), RunTracker()))
    assert cli.main(["experiment", "--repeats", "2"]) == 1
    assert len(list(offline.iterdir())) == 1  # no further runs after the first
    assert "1 failed, 7 not started" in capsys.readouterr().out


def test_missing_credentials_fail_before_creating_a_run(monkeypatch, tmp_path):
    for name in cli.CREDENTIAL_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(cli, "ENV_FILE", tmp_path / "missing.env")
    monkeypatch.setattr(runs, "RUNS_DIR", tmp_path / "runs")
    assert cli.main(["run"]) == 2
    assert not (tmp_path / "runs").exists()
