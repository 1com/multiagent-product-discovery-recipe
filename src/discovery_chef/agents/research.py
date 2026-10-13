"""Research synthesiser: interviews in (through retrieval), users and problems out."""

from __future__ import annotations

from discovery_chef.agents.common import (
    read_interview_tool,
    role_prompt,
    roster,
    search_interviews_tool,
)
from discovery_chef.agents.contracts import ResearchSynthesis
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import Conversation, LLMClient

NAME = "research_synthesiser"

JOB = """Your job: read the customer interviews and report who the users are, which problems \
are real, and where participants disagree. A separate analyst covers competitors and the \
market, so leave those out.

You have two tools. search_interviews returns ranked passages for a query. read_interview \
returns every turn of one interview. Each passage shows its citation ID, evidence tier and \
weight, target fit, and any sentences that also appear word for word in other interviews.

How to work:
- Find the themes yourself. Search for problems, current workarounds, requirements on a \
solution, and objections. Look for counter-evidence as hard as for support.
- Read the full transcript of every primary-tier interview at least once.
- An insight's strength depends on how many distinct usable interviews support it in their \
own words, their tiers, and whether the support is behaviour or stated preference. Support \
that rests only on templated sentences is weak.
- Excluded interviews are not evidence. Out-of-target interviews are contrast only.
- Willingness to pay: report the range and its conditions. It is stated intent, not demand."""


def run(llm: LLMClient, ctx: DiscoveryContext) -> ResearchSynthesis:
    conversation = Conversation(
        system=role_prompt("research synthesiser", JOB, ctx, eda_questions=("Q1", "Q2", "Q3")),
    ).say(
        f"Target customer from the idea brief: {ctx.dataset.idea.target_customer}\n\n"
        f"Interview roster from the EDA:\n{roster(ctx)}\n\n"
        "Investigate the interviews with your tools, then return the research synthesis."
    )
    return llm.run(agent=NAME, step="synthesis", conversation=conversation,
                   output_type=ResearchSynthesis,
                   tools=[search_interviews_tool(ctx), read_interview_tool(ctx)])
