"""Critic: checks each draft against the sources themselves, not the analysts' summaries."""

from __future__ import annotations

from discovery_chef.agents.common import get_sources_tool, role_prompt, search_interviews_tool
from discovery_chef.agents.contracts import Critique, DiscoveryBrief
from discovery_chef.citations import CitationReport
from discovery_chef.context import DiscoveryContext
from discovery_chef.llm import Conversation, LLMClient

NAME = "critic"

JOB = """Your job: review the draft discovery brief before it reaches the product team. \
Check it against the sources themselves, not against anyone's summary.

Check that:
- every claim about customers or the market cites a source, and the cited source actually \
supports it. Use get_sources to read what was cited, and search_interviews to look for \
counter-evidence the brief ignores.
- quotes are word for word and numbers trace to a source.
- no evidence from excluded interviews or unusable market snippets is presented as fact.
- strength is stated honestly. Claims resting only on templated sentences, stated \
preferences or a single interview are not presented as strong.
- the recommendation follows from the evidence, and all required sections are present.

Look sources up in batches: put every ID you want to check into one get_sources call (up \
to 20), and make several calls in one turn if needed. You have at most {budget} rounds of \
tool calls per review; then you must give your verdict with what you have checked.

An automated citation check has already run and its report is attached. Confirm or extend \
it; don't just repeat it.

Severity: blocker = factually wrong, invented, or relies on excluded evidence. major = an \
overclaim or an unsupported claim that matters to the decision. minor = wording, clarity or \
a small omission. Approve only when no blocker or major objection remains. Be specific: \
copy the excerpt, say what is wrong, say how to fix it. Don't object to style you merely \
would have written differently."""


class Critic:
    """Keeps one conversation across rounds so it can tell which objections were fixed."""

    def __init__(self, llm: LLMClient, ctx: DiscoveryContext):
        self.llm = llm
        self.ctx = ctx
        self.conversation = Conversation(system=role_prompt(
            "critic", JOB.format(budget=llm.config.max_tool_rounds), ctx, eda_questions=()))

    def review(self, brief: DiscoveryBrief, report: CitationReport, round_number: int
               ) -> Critique:
        intro = ("Review this draft." if round_number == 0 else
                 "The writer revised the brief. Review the new version and list which of "
                 "your earlier objections are now resolved.")
        self.conversation.say(
            f"{intro}\n\n<draft round=\"{round_number}\" recommendation="
            f"\"{brief.recommendation}\">\n{brief.markdown}\n</draft>\n\n{report.render()}"
        )
        return self.llm.run(agent=NAME, step=f"review-{round_number}",
                            conversation=self.conversation, output_type=Critique,
                            tools=[get_sources_tool(self.ctx), search_interviews_tool(self.ctx)])
