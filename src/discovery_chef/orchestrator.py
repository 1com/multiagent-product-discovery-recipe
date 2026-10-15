"""Orchestrator: a code-driven pipeline with one parallel stage and a critic loop.

    research synthesiser ─┐
                          ├─> risk analyst ─> brief writer ─> critic ─┐
    market analyst ───────┘                        ^                  │ revise
                                                   └──────────────────┘ (at most N rounds)

Why this pattern: the work has a fixed dependency graph. The two analysts need different
inputs and nothing from each other, so they run in parallel. The risk analyst needs both,
and the writer needs all three. An LLM supervisor would only re-decide that fixed order on
every run, adding cost and variance. Iteration pays off at the end, where a critic checks
the draft against the sources and the writer revises.

Loop control (where agents can loop or drift):
- approved: the critic approves AND the deterministic citation check passes. A model's
  "approve" never overrides a failed check.
- revision_limit: the cap was reached; unresolved objections stay in review.md.
- stalled: a revision did not reduce blocker + major objections, so stop rather than churn.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Protocol

from discovery_chef.agents import market, research, risk
from discovery_chef.agents.contracts import (
    Critique,
    DiscoveryBrief,
    MarketAnalysis,
    ResearchSynthesis,
    RiskAnalysis,
)
from discovery_chef.agents.critic import Critic
from discovery_chef.agents.writer import BriefWriter
from discovery_chef.citations import CitationReport, check_brief
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import LLM
from discovery_chef.runs import RunRecorder


@dataclass
class ReviewRound:
    round: int
    recommendation: str
    verdict: str
    blockers: int
    majors: int
    minors: int
    citation_check: dict

    @property
    def serious(self) -> int:
        return self.blockers + self.majors


class Reviser(Protocol):
    """Whoever wrote the draft and now revises it: the brief writer, or the single prompt."""

    def revise(self, critique: Critique, report: CitationReport, round_number: int
               ) -> DiscoveryBrief: ...


@dataclass
class ReviewResult:
    brief: DiscoveryBrief
    final_check: CitationReport
    loop_outcome: str
    rounds: list[ReviewRound]
    critiques: list[Critique]


@dataclass
class PipelineResult:
    research: ResearchSynthesis
    market: MarketAnalysis
    risk: RiskAnalysis
    brief: DiscoveryBrief
    final_check: CitationReport
    loop_outcome: str
    rounds: list[ReviewRound] = field(default_factory=list)
    critiques: list[Critique] = field(default_factory=list)


def run_pipeline(llm: LLM, ctx: DiscoveryContext, recorder: RunRecorder | None = None,
                 *, max_revisions: int = 2) -> PipelineResult:
    def save(name, data):
        if recorder:
            recorder.json(name, data)

    def run_and_save(agent, name):
        output = agent.run(llm, ctx)
        save(name, output)  # saved as soon as it is done, even if the other analyst fails
        return output

    with ThreadPoolExecutor(max_workers=2) as pool:
        research_future = pool.submit(run_and_save, research,
                                      "agents/research_synthesis.json")
        market_future = pool.submit(run_and_save, market, "agents/market_analysis.json")
        research_out, market_out = research_future.result(), market_future.result()

    risk_out = risk.run(llm, ctx, research_out, market_out)
    save("agents/risk_analysis.json", risk_out)

    writer = BriefWriter(llm, ctx)
    brief = writer.draft(research_out, market_out, risk_out)
    review = review_loop(llm, ctx, brief, writer, recorder, max_revisions=max_revisions)
    return PipelineResult(
        research=research_out, market=market_out, risk=risk_out, brief=review.brief,
        final_check=review.final_check, loop_outcome=review.loop_outcome,
        rounds=review.rounds, critiques=review.critiques,
    )


def review_loop(llm: LLM, ctx: DiscoveryContext, brief: DiscoveryBrief, reviser: Reviser,
                recorder: RunRecorder | None = None, *, max_revisions: int = 2
                ) -> ReviewResult:
    """The critic reviews each draft until it approves, the cap is reached or it stalls.

    Shared by the multi-agent pipeline and the single prompt with a critic, so the two
    systems differ only in how the first draft was written.
    """
    critic = Critic(llm, ctx)
    rounds: list[ReviewRound] = []
    critiques: list[Critique] = []
    outcome = "revision_limit"
    for number in range(max_revisions + 1):
        report = check_brief(brief.markdown, ctx)
        critique = critic.review(brief, report, number)
        critiques.append(critique)
        severities = [o.severity for o in critique.objections]
        rounds.append(ReviewRound(
            round=number, recommendation=brief.recommendation, verdict=critique.verdict,
            blockers=severities.count("blocker"), majors=severities.count("major"),
            minors=severities.count("minor"), citation_check=report.to_dict(),
        ))
        if recorder:
            recorder.text(f"review/round-{number}/brief.md", brief.markdown)
            recorder.json(f"review/round-{number}/citation_check.json", report.to_dict())
            recorder.json(f"review/round-{number}/critique.json", critique)

        if critique.verdict == "approve" and report.passed:
            outcome = "approved"
            break
        if number == max_revisions:
            outcome = "revision_limit"
            break
        if number > 0 and rounds[-1].serious >= rounds[-2].serious:
            outcome = "stalled"
            break
        brief = reviser.revise(critique, report, number + 1)

    return ReviewResult(brief=brief, final_check=check_brief(brief.markdown, ctx),
                        loop_outcome=outcome, rounds=rounds, critiques=critiques)


def review_markdown(result: PipelineResult | ReviewResult) -> str:
    """The critic's objections round by round, for the demo and the presentation."""
    lines = ["# Review log", "", f"Loop outcome: **{result.loop_outcome}** after "
             f"{len(result.rounds)} review round(s).", ""]
    for round_, critique in zip(result.rounds, result.critiques, strict=True):
        check = round_.citation_check
        lines += [
            f"## Round {round_.round}: {critique.verdict}",
            "",
            f"Recommendation in this draft: {round_.recommendation}. Objections: "
            f"{round_.blockers} blocker, {round_.majors} major, {round_.minors} minor. "
            f"Citation check: {'passed' if check['passed'] else 'failed'} "
            f"({check['blocking']} blocking, coverage {check['coverage']:.0%}).",
            "",
            critique.summary,
            "",
        ]
        if critique.resolved_from_previous:
            lines += ["Resolved from the previous round: "
                      + "; ".join(critique.resolved_from_previous), ""]
        for o in critique.objections:
            lines.append(f"- **{o.severity}** ({o.category}, {o.section}): \"{o.excerpt}\"  \n"
                         f"  {o.problem} *Fix:* {o.fix}")
        lines.append("")
    return "\n".join(lines)
