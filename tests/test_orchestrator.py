"""Pipeline wiring and critic-loop control, with a fake LLM standing in for every agent."""

import threading

import pytest

from discovery_chef.agents.contracts import (
    Critique,
    DiscoveryBrief,
    MarketAnalysis,
    Objection,
    ResearchSynthesis,
    RiskAnalysis,
)
from discovery_chef.baseline import build_conversation
from discovery_chef.orchestrator import review_markdown, run_pipeline
from discovery_chef.runs import RunRecorder

RESEARCH = ResearchSynthesis(segments=[], insights=[], disagreements=[],
                             willingness_to_pay="low", willingness_to_pay_evidence=[],
                             evidence_set_aside=["P06 excluded"])
MARKET = MarketAnalysis(competitors=[], white_space=[], pricing_anchors="EUR 2.99-6.99",
                        market_figures=[], idea_claim_checks=[])
RISK = RiskAnalysis(assumptions=[], riskiest_assumptions=[], experiments=[], open_questions=[],
                    suggested_recommendation="test_further", recommendation_reason="weak WTP")


def objection(severity):
    return Objection(id="O1", severity=severity, category="overclaim", section="3",
                     excerpt="x", problem="too strong", fix="soften")


class FakeLLM:
    def __init__(self, brief_markdown, critiques):
        self.brief = brief_markdown
        self.critiques = list(critiques)
        self.calls = []
        self.threads = {}

    def run(self, *, agent, step, conversation, output_type, tools=()):
        self.calls.append((agent, step))
        self.threads[agent] = threading.current_thread().name
        if output_type is ResearchSynthesis:
            return RESEARCH
        if output_type is MarketAnalysis:
            return MARKET
        if output_type is RiskAnalysis:
            return RISK
        if output_type is DiscoveryBrief:
            return DiscoveryBrief(recommendation="test_further", one_line_rationale="r",
                                  markdown=self.brief)
        if output_type is Critique:
            return self.critiques.pop(0)
        raise AssertionError(output_type)


def critique(verdict, *severities):
    return Critique(verdict=verdict, summary="s", objections=[objection(s) for s in severities],
                    resolved_from_previous=[])


def test_approved_on_first_review(ctx, passing_brief, tmp_path):
    llm = FakeLLM(passing_brief, [critique("approve", "minor")])
    recorder = RunRecorder("agents", root=tmp_path, run_id="r1")
    result = run_pipeline(llm, ctx, recorder)
    assert result.loop_outcome == "approved"
    agents = [a for a, _ in llm.calls]
    assert set(agents[:2]) == {"research_synthesiser", "market_analyst"}  # parallel stage
    assert agents[2:] == ["risk_analyst", "brief_writer", "critic"]
    # the two analysts ran on worker threads, not the main thread
    assert llm.threads["research_synthesiser"] != threading.main_thread().name
    for name in ("agents/research_synthesis.json", "agents/market_analysis.json",
                 "agents/risk_analysis.json", "review/round-0/brief.md",
                 "review/round-0/critique.json", "review/round-0/citation_check.json"):
        assert (tmp_path / "r1" / name).exists(), name
    assert "Round 0: approve" in review_markdown(result)


def test_failed_citation_check_overrides_critic_approval(ctx, passing_brief):
    broken = passing_brief.replace("[P02:t4]", "[P99:t4]")
    llm = FakeLLM(broken, [critique("approve"), critique("approve"), critique("approve")])
    result = run_pipeline(llm, ctx, max_revisions=2)
    assert result.loop_outcome != "approved"
    assert ("brief_writer", "revision-1") in llm.calls


def test_revision_limit(ctx, passing_brief):
    llm = FakeLLM(passing_brief, [critique("revise", "major", "major"),
                                  critique("revise", "major"),
                                  critique("revise", "minor")])
    result = run_pipeline(llm, ctx, max_revisions=2)
    assert result.loop_outcome == "revision_limit"
    assert len(result.rounds) == 3
    assert [r.serious for r in result.rounds] == [2, 1, 0]


def test_stalled_when_revisions_do_not_help(ctx, passing_brief):
    llm = FakeLLM(passing_brief, [critique("revise", "major"),
                                  critique("revise", "major", "blocker")])
    result = run_pipeline(llm, ctx, max_revisions=3)
    assert result.loop_outcome == "stalled"
    assert len(result.rounds) == 2


@pytest.mark.parametrize("variant", ["naive", "informed"])
def test_baseline_prompt_variants(ctx, variant):
    conversation = build_conversation(ctx, variant)
    prompt = conversation.system + conversation.messages[0].parts[0].text
    assert 'id="P02:t4"' in prompt and "C:MealLoop" in prompt and 'id="S08"' in prompt
    has_eda = "exploratory data analysis" in prompt and 'tier="excluded"' in prompt
    assert has_eda == (variant == "informed")
