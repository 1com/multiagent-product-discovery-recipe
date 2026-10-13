"""Phase 3 evaluation on fake run folders with a fake judge (no API calls)."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from discovery_chef.eval.collect import collect
from discovery_chef.eval.judge import excerpt_in_brief, judge
from discovery_chef.eval.report import blind_id, evaluate
from discovery_chef.eval.rubric import (
    CRITERIA,
    TRAPS,
    CriterionScore,
    JudgeVerdict,
    Misrepresentation,
    TrapAssessment,
    faithfulness,
    quality_index,
)

MODEL = "gemini-3.8-flash"
PRINT = "abc123"


def call(agent, step, cost, latency):
    return {"agent": agent, "step": step, "cost_usd": cost, "latency_s": latency}


def make_run(runs_dir, run_id, mode, brief, *, model=MODEL, fingerprint=PRINT, error=False):
    run_dir = runs_dir / run_id
    (run_dir / "review" / "round-0").mkdir(parents=True)
    (run_dir / "brief.md").write_text(brief)
    calls = [call("single_prompt", "brief", 0.02, 30.0)]
    config = {"model": model, "code_fingerprint": fingerprint}
    config |= {"max_revisions": 2} if mode == "agents" else {"variant": mode.split("-")[-1]}
    run = {"run_id": run_id, "mode": mode, "recommendation": "test_further", "config": config}
    if mode == "agents":
        calls = [call("research_synthesiser", "synthesis", 0.10, 100.0),
                 call("brief_writer", "draft", 0.05, 50.0),
                 call("critic", "review-0", 0.04, 20.0),
                 call("brief_writer", "revision-1", 0.05, 40.0),
                 call("critic", "review-1", 0.03, 10.0)]
        (run_dir / "review" / "round-0" / "brief.md").write_text(brief + "\nDraft only.")
        (run_dir / "review" / "round-1").mkdir()
        critique = {"verdict": "revise", "objections": [
            {"severity": "blocker", "category": "invented_number", "section": "7",
             "problem": "made-up %"}]}
        (run_dir / "review" / "round-0" / "critique.json").write_text(json.dumps(critique))
        (run_dir / "review" / "round-1" / "critique.json").write_text(
            json.dumps({"verdict": "approve", "objections": []}))
        run |= {"loop_outcome": "approved", "rounds": [
            {"round": 0, "recommendation": "build", "verdict": "revise", "blockers": 1,
             "majors": 0, "minors": 0, "citation_check": {"blocking": 2}},
            {"round": 1, "recommendation": "test_further", "verdict": "approve",
             "blockers": 0, "majors": 0, "minors": 0, "citation_check": {"blocking": 0}}]}
    total_cost = round(sum(c["cost_usd"] for c in calls), 6)
    total_time = sum(c["latency_s"] for c in calls) + 5
    (run_dir / "usage.json").write_text(json.dumps({"totals": {
        "cost_usd": total_cost, "wall_clock_s": total_time, "calls": len(calls)},
        "calls": calls}))
    (run_dir / "config.json").write_text(json.dumps(run["config"]))
    if error:
        (run_dir / "error.json").write_text(json.dumps(
            {"type": "LLMError", "message": "critic: still calling tools after 12 rounds"}))
    else:
        (run_dir / "run.json").write_text(json.dumps(run))
    return run_dir


@pytest.fixture
def runs(tmp_path, passing_brief):
    runs_dir = tmp_path / "runs"
    make_run(runs_dir, "r1-baseline-naive", "baseline-naive", passing_brief)
    make_run(runs_dir, "r2-baseline-informed", "baseline-informed", passing_brief)
    make_run(runs_dir, "r3-agents", "agents", passing_brief)
    make_run(runs_dir, "r4-old", "baseline-naive", passing_brief, fingerprint="old")
    make_run(runs_dir, "r5-lite", "baseline-naive", passing_brief, model="gemini-3.5-flash-lite")
    make_run(runs_dir, "r6-failed", "agents", passing_brief, error=True)
    return runs_dir


class FakeJudge:
    """Claims every trap handled; one excerpt is invented and must be rejected."""

    def __init__(self, brief):
        self.config = SimpleNamespace(model="judge-model")
        self.brief = brief
        self.calls = 0

    def run(self, *, agent, step, conversation, output_type, tools=()):
        self.calls += 1
        traps = [TrapAssessment(trap_id=t.id, handled=True,
                                excerpt="We bought basil twice in one week")
                 for t in TRAPS]
        traps[1] = TrapAssessment(trap_id="T02", handled=True,
                                  excerpt="this sentence is not in the brief at all")
        criteria = [CriterionScore(criterion_id=c.id, score=4, justification="ok")
                    for c in CRITERIA]
        criteria[0] = CriterionScore(criterion_id="C1", score=9, justification="too high")
        misrepresentations = [
            Misrepresentation(excerpt="EUR 3.50 per month according to the pricing study",
                              source_id="S05", problem="real excerpt, counted"),
            Misrepresentation(excerpt="an excerpt the brief never contains",
                              source_id="S01", problem="invented, must be dropped")]
        return JudgeVerdict(weaknesses=["thin on pricing"],
                            misrepresentations=misrepresentations, traps=traps,
                            criteria=criteria)


def test_collect_selects_comparable_finished_runs(runs):
    records, skipped = collect(runs, model=MODEL, fingerprint=PRINT)
    assert sorted(r.condition for r in records) == ["agents", "agents_draft", "informed",
                                                    "naive"]
    reasons = {s.run_id: s.reason for s in skipped}
    assert reasons["r4-old"] == "made with different code or prompts"
    assert reasons["r5-lite"].startswith("model")
    failed = next(s for s in skipped if s.run_id == "r6-failed")
    assert failed.failed and failed.system == "agents" and failed.cost_usd > 0
    assert reasons["r6-failed"].startswith("failed: LLMError")
    assert len(collect(runs, model=MODEL, fingerprint=None)[0]) == 5  # old code accepted


def test_draft_is_costed_as_if_the_run_stopped_before_the_critic(runs):
    records, _ = collect(runs, model=MODEL, fingerprint=PRINT)
    draft = next(r for r in records if r.condition == "agents_draft")
    final = next(r for r in records if r.condition == "agents")
    assert draft.cost_usd == pytest.approx(0.15) and final.cost_usd == pytest.approx(0.27)
    assert draft.wall_clock_s == pytest.approx(final.wall_clock_s - 70)
    assert (draft.calls, draft.recommendation) == (2, "build")
    assert draft.markdown.endswith("Draft only.")


def test_judge_claims_are_verified_and_cached(runs, ctx, tmp_path):
    from discovery_chef.citations import check_brief

    records, _ = collect(runs, model=MODEL, fingerprint=PRINT)
    record = records[0]
    fake = FakeJudge(record.markdown)
    report = check_brief(record.markdown, ctx)
    first = judge(fake, record, report, tmp_path / "cache", model="judge-model",
                  sources="SOURCES")
    assert first.traps["T01"] is True
    assert first.traps["T02"] is False  # invented excerpt rejected
    assert first.criteria["C1"] == 5  # clamped to the scale
    assert len(first.misrepresentations) == 1 and first.faithfulness == 0.75
    assert first.unverified_claims == 2  # one trap excerpt, one misrepresentation
    again = judge(None, record, report, tmp_path / "cache", model="judge-model",
                  sources="SOURCES")
    assert again.traps == first.traps and fake.calls == 1


def test_citation_check_vetoes_the_judge(runs, ctx, tmp_path, passing_brief):
    from discovery_chef.citations import check_brief

    bad = passing_brief.replace("[P02:t4, P04:t4]", "[P02:t4, P04:t4, P06:t9]")
    assert bad != passing_brief
    records, _ = collect(runs, model=MODEL, fingerprint=PRINT)
    record = records[0].__class__(**{**records[0].__dict__, "markdown": bad})
    verdict = judge(FakeJudge(bad), record, check_brief(bad, ctx), tmp_path / "cache",
                    model="judge-model", sources="SOURCES")
    assert verdict.traps["T01"] is False


def test_excerpt_matching():
    brief = "Line one.\nThe 97% figure comes from a blog and is unreliable."
    assert excerpt_in_brief("the 97% figure comes from a blog", brief)
    assert excerpt_in_brief("The 97% figure ... is unreliable", brief)
    assert not excerpt_in_brief("97% would pay", brief)
    assert not excerpt_in_brief("", brief)


def test_full_evaluation_writes_report_and_blind_kit(runs, ctx, tmp_path):
    records, skipped = collect(runs, model=MODEL, fingerprint=PRINT)
    out = tmp_path / "eval"
    result = evaluate(records, ctx, runs, out, judge_llm=FakeJudge(""), judge_model="judge-model",
                      cache_dir=out / "judge", skipped=skipped, setup={"model": MODEL})
    assert list(result.summary["condition"]) == ["naive", "informed", "agents_draft", "agents"]
    assert result.scores["quality_index"].notna().all()
    assert set(result.objections["category"]) == {"invented_number"}
    assert list(result.loops["verdict"]) == ["revise", "approve"]
    report = (out / "eval_report.md").read_text()
    assert "What each step adds" in report and "The critic loop" in report
    assert "Runs that failed" in report and "r6-failed" in report
    assert (out / "figures" / "quality_vs_cost.png").exists()
    details = json.loads((out / "judgements.json").read_text())
    assert all(d["weaknesses"] == ["thin on pricing"] for d in details.values())
    assert "Sources misrepresented" in report
    blind = json.loads((out / "blind" / "key.json").read_text())
    assert len(blind) == 4 and all(b.startswith("B") for b in blind)
    assert blind[blind_id("r3-agents")] == "r3-agents"


def test_human_scores_are_compared_with_the_judge(runs, ctx, tmp_path):
    records, skipped = collect(runs, model=MODEL, fingerprint=PRINT)
    out = tmp_path / "eval"
    kwargs = dict(judge_model="judge-model", cache_dir=out / "judge", skipped=skipped,
                  setup={})
    evaluate(records, ctx, runs, out, judge_llm=FakeJudge(""), **kwargs)
    human = pd.DataFrame([{"blind_id": blind_id("r1-baseline-naive"), "C1": 5, "C2": 2,
                           "C3": 4, "C4": 4, "C5": 4, "notes": ""}])
    human.to_csv(out / "blind" / "human_scores.csv", index=False)
    result = evaluate(records, ctx, runs, out, judge_llm=None, **kwargs)  # cached verdicts
    agreement = result.agreement.set_index("criterion")
    assert agreement.loc["C2", "mean_abs_difference"] == 2  # judge said 4
    assert agreement.loc["C3", "exact_agreement"] == 1


def test_quality_index_and_faithfulness():
    assert quality_index(1.0, 5.0, 1.0) == 1.0
    assert quality_index(0.0, 1.0, 0.0) == 0.0
    assert quality_index(0.5, 3.0, 0.5) == 0.5
    assert [faithfulness(n) for n in (0, 1, 4, 9)] == [1.0, 0.75, 0.0, 0.0]
