"""Single-prompt baseline: the same task, the same data and the same brief format, in one call.

Two variants separate what the agents add from what the EDA adds:
- naive:    raw data and the task. No EDA rules, no evidence tiers.
- informed: also gets the EDA rules, the interview roster with tiers, and the source checks,
            i.e. the same knowledge the agents get, minus the decomposition and the critic.
"""

from __future__ import annotations

from typing import Literal

from discovery_chef.agents.common import (
    BRIEF_FORMAT,
    PRODUCT,
    competitor_sources,
    ground_rules,
    idea_source,
    roster,
)
from discovery_chef.agents.contracts import DiscoveryBrief
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import Conversation, LLMClient

Variant = Literal["naive", "informed"]
NAME = "single_prompt"


def _interviews(ctx: DiscoveryContext, informed: bool) -> str:
    if informed:
        return "\n".join(p.render() for p in ctx.index.passages)
    blocks = []
    for interview in ctx.dataset.interviews.values():
        for turn in interview.turns:
            blocks.append(
                f'<source id="{interview.id}:t{turn.number}" type="interview_turn">\n'
                f"Interviewer: {turn.question}\nParticipant: {turn.answer}\n</source>"
            )
    return "\n".join(blocks)


def _snippets(ctx: DiscoveryContext, informed: bool) -> str:
    if informed:
        return "\n".join(ctx.source_text(sid) for sid in ctx.dataset.snippets)
    return "\n".join(
        f'<source id="{s.id}" type="market_snippet">\nClaim: {s.claim}\nStat: {s.stat}\n'
        f"Source: {s.source_name or 'none'} ({s.year or 'no year'})\n</source>"
        for s in ctx.dataset.snippets.values()
    )


def build_conversation(ctx: DiscoveryContext, variant: Variant) -> Conversation:
    informed = variant == "informed"
    system = (
        f"You are a product discovery analyst. Your team is deciding whether and how to "
        f"build {PRODUCT}. From the research data provided, write a validated discovery "
        f"brief: who the users are, which problems are real, what the evidence says, what "
        f"the risks and open assumptions are, and what to test next.\n\n"
        f"{ground_rules(ctx, eda_questions=() if informed else None)}\n\n{BRIEF_FORMAT}"
    )
    personas = "\n".join(f"- {i.id}: {i.persona} (interviewed {i.date})"
                         for i in ctx.dataset.interviews.values())
    parts = [idea_source(ctx), f"Interview participants:\n{personas}"]
    if informed:
        parts.append(f"Interview roster with evidence tiers from the EDA:\n{roster(ctx)}")
    parts += [
        f"Interview transcripts, one source per turn:\n{_interviews(ctx, informed)}",
        f"Competitor rows (competitors.csv):\n{competitor_sources(ctx)}",
        f"Market snippets (market_snippets.json):\n{_snippets(ctx, informed)}",
        "Write the discovery brief.",
    ]
    return Conversation(system=system).say("\n\n".join(parts))


def run_baseline(llm: LLMClient, ctx: DiscoveryContext, variant: Variant) -> DiscoveryBrief:
    return llm.run(agent=f"{NAME}_{variant}", step="brief",
                   conversation=build_conversation(ctx, variant), output_type=DiscoveryBrief)
