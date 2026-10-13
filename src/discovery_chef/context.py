"""Everything a Phase 2 run reads: the dataset, the EDA profile and the interview index.

A run refuses to start on a missing or stale EDA profile, so agents never act on rules
derived from different data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from discovery_chef.dataset import Dataset, load_dataset
from discovery_chef.eda.profile import SCHEMA_VERSION, data_checksums
from discovery_chef.paths import DATA_DIR, EDA_PROFILE_PATH
from discovery_chef.retrieval import InterviewIndex

INTERVIEW_TURN = re.compile(r"^(P\d{2}):t(\d{1,2})$")
IDEA_BRIEF = "idea_brief"  # citation ID of data/idea_brief.md


class StaleProfileError(RuntimeError):
    pass


@dataclass
class DiscoveryContext:
    dataset: Dataset
    profile: dict
    index: InterviewIndex

    # --- EDA hand-off ---------------------------------------------------------------------

    def rules(self, *questions: str) -> list[str]:
        """'So the agent will ...' rules from the EDA, optionally limited to questions."""
        return [
            f"{f['id']}: {f['so_the_agent_will']}"
            for f in self.profile["findings"]
            if not questions or f["question"] in questions
        ]

    def findings(self, *questions: str) -> list[dict]:
        return [f for f in self.profile["findings"] if not questions or f["question"] in questions]

    def excluded_interviews(self) -> list[str]:
        return sorted(i for i, m in self.profile["interviews"].items()
                      if m["evidence_tier"] == "excluded")

    def citable_snippets(self) -> list[str]:
        return sorted(s for s, m in self.profile["market_snippets"].items()
                      if m["reliability"] in ("usable", "usable_with_caveat"))

    # --- citation IDs -----------------------------------------------------------------------

    def known_ids(self) -> set[str]:
        ids = set(self.dataset.interviews) | set(self.dataset.snippets)
        ids |= {f"C:{name}" for name in self.dataset.competitors}
        ids |= set(self.index.by_id)
        return ids | {IDEA_BRIEF}

    def source_text(self, source_id: str) -> str | None:
        """The text a citation points to, rendered as a <source> block."""
        if source_id == IDEA_BRIEF:
            return (f'<source id="{IDEA_BRIEF}" type="document">\n'
                    f"{self.dataset.idea.text.strip()}\n</source>")
        if source_id in self.index.by_id:
            return self.index.by_id[source_id].render()
        if source_id in self.dataset.interviews:
            interview = self.dataset.interviews[source_id]
            meta = self.profile["interviews"][source_id]
            return (f'<source id="{source_id}" type="interview_profile" '
                    f'tier="{meta["evidence_tier"]}">\nPersona: {interview.persona}\n'
                    f'Target fit: {meta["target_fit"]} ({meta["fit_rationale"]})\n</source>')
        if source_id in self.dataset.snippets:
            s = self.dataset.snippets[source_id]
            reliability = self.profile["market_snippets"][source_id]["reliability"]
            return (f'<source id="{s.id}" type="market_snippet" reliability="{reliability}">\n'
                    f"Claim: {s.claim}\nStat: {s.stat}\nSource: {s.source_name or 'none'} "
                    f"({s.year or 'no year'})\n</source>")
        if source_id.startswith("C:") and source_id[2:] in self.dataset.competitors:
            c = self.dataset.competitors[source_id[2:]]
            return (f'<source id="{source_id}" type="competitor_row">\n'
                    f"Positioning: {c.positioning}\nPricing: {c.pricing}\n"
                    f"Key features: {', '.join(c.key_features)}\nTarget user: {c.target_user}\n"
                    f"Source URL: {c.source_url or 'none'}\nLast verified: "
                    f"{c.last_verified or 'unknown'}\n</source>")
        return None

    def raw_text(self, source_id: str) -> str:
        """Plain text behind a citation, for verbatim quote checks."""
        if source_id == IDEA_BRIEF:
            return self.dataset.idea.text
        if source_id in self.index.by_id:
            passage = self.index.by_id[source_id]
            return f"{passage.question}\n{passage.answer}"
        if source_id in self.dataset.interviews:
            return self.dataset.interviews[source_id].text
        if source_id in self.dataset.snippets:
            s = self.dataset.snippets[source_id]
            return f"{s.claim}\n{s.stat}\n{s.source_name or ''}\n{s.year or ''}"
        if source_id.startswith("C:") and source_id[2:] in self.dataset.competitors:
            c = self.dataset.competitors[source_id[2:]]
            return "\n".join((c.name, c.positioning, c.pricing, ", ".join(c.key_features),
                              c.target_user, str(c.last_verified)))
        return ""


def load_context(profile_path: Path = EDA_PROFILE_PATH, data_dir: Path = DATA_DIR
                 ) -> DiscoveryContext:
    if not profile_path.exists():
        raise StaleProfileError(f"{profile_path} not found. Run `uv run discovery-chef eda` first.")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if profile.get("schema_version") != SCHEMA_VERSION:
        raise StaleProfileError(f"The EDA profile has schema version "
                                f"{profile.get('schema_version')}, expected {SCHEMA_VERSION}. "
                                "Run `uv run discovery-chef eda` again.")
    if profile.get("data_sha256") != data_checksums(data_dir):
        raise StaleProfileError("The EDA profile was built from different data. "
                                "Run `uv run discovery-chef eda` again.")
    dataset = load_dataset(data_dir)
    return DiscoveryContext(dataset=dataset, profile=profile,
                            index=InterviewIndex.build(dataset, profile))
