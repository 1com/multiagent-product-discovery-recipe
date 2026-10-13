"""Risk and assumption analyst: both analyses in, ranked assumptions and tests out."""

from __future__ import annotations

from discovery_chef.agents.common import as_json, idea_source, role_prompt
from discovery_chef.agents.contracts import MarketAnalysis, ResearchSynthesis, RiskAnalysis
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import LLM, Conversation

NAME = "risk_analyst"

JOB = """Your job: turn the research synthesis and the market analysis into the assumptions \
PantryPal depends on, rank them by risk, and design the cheapest tests that would settle \
the riskiest ones. You work from the two analysts' outputs; you don't see the raw data.

How to work:
- Cover desirability (do people want it), usability (can they use it, for example keeping \
an inventory current), viability (will they pay, can it compete) and feasibility.
- An assumption is risky when confidence is low and the impact if wrong is high.
- For each assumption, list the source IDs for and against, taken from the analysts' \
evidence. Never cite a source the analysts didn't.
- Experiments must be concrete: who, what, how many, and what result would change the \
decision.
- Name what the data cannot tell us as open questions rather than guessing.
- Suggest build, pivot or test further, with the reason."""


def run(llm: LLM, ctx: DiscoveryContext, research: ResearchSynthesis,
        market: MarketAnalysis) -> RiskAnalysis:
    gaps = "\n".join(f"- {f['finding']}" for f in ctx.findings("Q5"))
    conversation = Conversation(
        system=role_prompt("risk and assumption analyst", JOB, ctx,
                           eda_questions=("Q1", "Q3", "Q5")),
    ).say(
        f"{idea_source(ctx)}\n\nResearch synthesis (from the research synthesiser):\n"
        f"<analysis>\n{as_json(research)}\n</analysis>\n\nMarket analysis (from the "
        f"competitor and market analyst):\n<analysis>\n{as_json(market)}\n</analysis>\n\n"
        f"Known gaps in the data (from the EDA):\n{gaps}\n\nReturn the risk analysis."
    )
    return llm.run(agent=NAME, step="analysis", conversation=conversation,
                   output_type=RiskAnalysis)
