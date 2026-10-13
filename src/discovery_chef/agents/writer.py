"""Brief writer: the three analyses in, the discovery brief out; revises on critique."""

from __future__ import annotations

from discovery_chef.agents.common import BRIEF_FORMAT, as_json, idea_source, role_prompt
from discovery_chef.agents.contracts import (
    Critique,
    DiscoveryBrief,
    MarketAnalysis,
    ResearchSynthesis,
    RiskAnalysis,
)
from discovery_chef.citations import CitationReport
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import Conversation, LLMClient

NAME = "brief_writer"

JOB = f"""Your job: write the discovery brief for the PantryPal product team from the three \
analysts' work. Readers are a product manager, a designer and an engineering lead deciding \
whether to invest.

{BRIEF_FORMAT}

Use only the quotes, numbers and citation IDs that appear in the analysts' work, and copy \
quotes exactly. When you revise, fix every objection from the reviewer and every issue in \
the automated citation check, and leave the parts that were fine unchanged."""


class BriefWriter:
    """Keeps one conversation so each revision sees the draft history (append-only)."""

    def __init__(self, llm: LLMClient, ctx: DiscoveryContext):
        self.llm = llm
        self.conversation = Conversation(system=role_prompt("brief writer", JOB, ctx,
                                                            eda_questions=()))
        self.ctx = ctx

    def draft(self, research: ResearchSynthesis, market: MarketAnalysis,
              risk: RiskAnalysis) -> DiscoveryBrief:
        self.conversation.say(
            f"{idea_source(self.ctx)}\n\n"
            f"Research synthesis:\n<analysis>\n{as_json(research)}\n</analysis>\n\n"
            f"Market analysis:\n<analysis>\n{as_json(market)}\n</analysis>\n\n"
            f"Risk analysis:\n<analysis>\n{as_json(risk)}\n</analysis>\n\n"
            "Write the discovery brief."
        )
        return self.llm.run(agent=NAME, step="draft", conversation=self.conversation,
                            output_type=DiscoveryBrief)

    def revise(self, critique: Critique, report: CitationReport, round_number: int
               ) -> DiscoveryBrief:
        objections = "\n".join(
            f"- [{o.severity}] {o.id} ({o.category}, {o.section}): \"{o.excerpt}\" - "
            f"{o.problem} Fix: {o.fix}"
            for o in critique.objections
        ) or "- none"
        self.conversation.say(
            f"The reviewer's verdict: {critique.verdict}. {critique.summary}\n\n"
            f"Objections:\n{objections}\n\n{report.render()}\n\n"
            "Revise the brief and return the complete new version."
        )
        return self.llm.run(agent=NAME, step=f"revision-{round_number}",
                            conversation=self.conversation, output_type=DiscoveryBrief)
