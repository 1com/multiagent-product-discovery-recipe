"""Competitor and market analyst: competitor rows and market snippets in, landscape out."""

from __future__ import annotations

from discovery_chef.agents.common import (
    competitor_sources,
    idea_source,
    role_prompt,
    snippet_sources,
)
from discovery_chef.agents.contracts import MarketAnalysis
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import LLM, Conversation

NAME = "market_analyst"

JOB = """Your job: assess the competitor landscape and the market statistics, and check the \
idea brief's claims about the market and existing apps. You don't see the customer \
interviews; another analyst covers customers.

How to work:
- For each competitor: which parts of the PantryPal promise it already covers, what it \
charges, how current and well-sourced its row is, and how much of a threat it is.
- For each market snippet: whether it can back a claim, and how to use it if so.
- Check every claim in the idea brief about the market or existing apps.
- White space: what no competitor offers, citing the rows that show the gap.
- Prices are list prices from the rows; annual plans may be converted to per month, but \
say so."""


def run(llm: LLM, ctx: DiscoveryContext) -> MarketAnalysis:
    reliability = "\n".join(
        f"- {sid}: {meta['reliability']} ({'; '.join(meta['issues']) or 'no issues'})"
        for sid, meta in ctx.profile["market_snippets"].items()
    )
    freshness = "\n".join(
        f"- C:{name}: {meta['freshness']}, last verified {meta['last_verified']}"
        f"{' (' + '; '.join(meta['issues']) + ')' if meta['issues'] else ''}"
        for name, meta in ctx.profile["competitors"].items()
    )
    conversation = Conversation(
        system=role_prompt("competitor and market analyst", JOB, ctx, eda_questions=("Q4",)),
    ).say(
        f"{idea_source(ctx)}\n\nCompetitor rows (competitors.csv; research date "
        f"{ctx.profile['as_of']}):\n{competitor_sources(ctx)}\n\nMarket snippets "
        f"(market_snippets.json):\n{snippet_sources(ctx)}\n\nEDA checks on the snippets:\n"
        f"{reliability}\n\nEDA checks on the competitor rows:\n{freshness}\n\n"
        "Return the market analysis."
    )
    return llm.run(agent=NAME, step="analysis", conversation=conversation,
                   output_type=MarketAnalysis)
