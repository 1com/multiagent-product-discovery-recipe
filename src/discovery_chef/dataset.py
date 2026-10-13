"""Load the fixed PantryPal research dataset from `data/`.

The files under `data/` are read-only inputs: nothing in this package writes to them.
Text inside interviews and documents is data, never instructions.

Citation IDs used throughout the project:
- interviews: the `interview_id` in each transcript's front matter (P01-P10)
- competitors: the `name` column of competitors.csv (e.g. "FridgeChef")
- market snippets: S01-S09, assigned by position in market_snippets.json
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from discovery_chef.paths import DATA_DIR

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> tuple[str, ...]:
    return tuple(s.strip() for s in _SENTENCE_BOUNDARY.split(text.strip()) if s.strip())


@dataclass(frozen=True)
class Turn:
    number: int
    question: str
    answer: str

    @property
    def answer_sentences(self) -> tuple[str, ...]:
        return split_sentences(self.answer)


@dataclass(frozen=True)
class Interview:
    id: str
    persona: str
    date: date
    turns: tuple[Turn, ...]
    text: str  # the raw file, used to check that quotes are verbatim

    def contains(self, quote: str) -> bool:
        return quote in self.text

    @property
    def participant_words(self) -> int:
        return sum(len(turn.answer.split()) for turn in self.turns)


@dataclass(frozen=True)
class Competitor:
    name: str
    positioning: str
    pricing: str
    key_features: tuple[str, ...]
    target_user: str
    source_url: str | None
    last_verified: date | None


@dataclass(frozen=True)
class MarketSnippet:
    id: str
    claim: str
    stat: str
    source_name: str | None
    source_url: str | None
    year: int | None


@dataclass(frozen=True)
class IdeaBrief:
    text: str
    target_customer: str


@dataclass(frozen=True)
class Dataset:
    idea: IdeaBrief
    interviews: dict[str, Interview]
    competitors: dict[str, Competitor]
    snippets: dict[str, MarketSnippet]

    @property
    def as_of(self) -> date:
        """Reference date for freshness checks: the last interview date.

        Using the research date instead of today's clock keeps every run reproducible.
        """
        return max(interview.date for interview in self.interviews.values())


def load_dataset(data_dir: Path = DATA_DIR) -> Dataset:
    if not data_dir.is_dir():
        raise FileNotFoundError(
            f"Data directory not found: {data_dir}. Run from a repository checkout "
            "installed with `uv sync`."
        )
    return Dataset(
        idea=load_idea_brief(data_dir / "idea_brief.md"),
        interviews=load_interviews(data_dir / "interviews"),
        competitors=load_competitors(data_dir / "competitors.csv"),
        snippets=load_market_snippets(data_dir / "market_snippets.json"),
    )


def load_idea_brief(path: Path) -> IdeaBrief:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\*\*Target customer:\*\*\s*(.+)", text)
    if not match:
        raise ValueError(f"{path}: no '**Target customer:**' line")
    return IdeaBrief(text=text, target_customer=match.group(1).strip())


def load_interviews(directory: Path) -> dict[str, Interview]:
    interviews = [parse_interview(path) for path in sorted(directory.glob("*.md"))]
    if not interviews:
        raise FileNotFoundError(f"No interview transcripts in {directory}")
    return {interview.id: interview for interview in interviews}


def parse_interview(path: Path) -> Interview:
    text = path.read_text(encoding="utf-8")
    front, body = _split_front_matter(text, path)
    interview_id = front["interview_id"]
    if interview_id != path.stem:
        raise ValueError(f"{path}: interview_id {interview_id!r} does not match file name")

    turns: list[Turn] = []
    question: str | None = None
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        speaker, _, utterance = line.partition(":")
        if speaker == "Interviewer":
            if question is not None:
                raise ValueError(f"{path}: two interviewer lines in a row")
            question = utterance.strip()
        elif speaker == "Participant":
            if question is None:
                raise ValueError(f"{path}: participant line without a question")
            turns.append(Turn(number=len(turns) + 1, question=question, answer=utterance.strip()))
            question = None
        else:
            raise ValueError(f"{path}: unrecognised line {line[:40]!r}")
    if question is not None:
        raise ValueError(f"{path}: final question has no answer")

    return Interview(
        id=interview_id,
        persona=front["participant_persona"],
        date=date.fromisoformat(front["date"]),
        turns=tuple(turns),
        text=text,
    )


def _split_front_matter(text: str, path: Path) -> tuple[dict[str, str], str]:
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f"{path}: missing '---' front matter")
    fields = {}
    for line in parts[1].strip().splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, parts[2]


def load_competitors(path: Path) -> dict[str, Competitor]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    competitors = {}
    for row in rows:
        competitor = Competitor(
            name=row["name"].strip(),
            positioning=row["positioning"].strip(),
            pricing=row["pricing"].strip(),
            key_features=tuple(f.strip() for f in row["key_features"].split(",") if f.strip()),
            target_user=row["target_user"].strip(),
            source_url=row["source_url"].strip() or None,
            last_verified=date.fromisoformat(v) if (v := row["last_verified"].strip()) else None,
        )
        competitors[competitor.name] = competitor
    if len(competitors) != len(rows):
        raise ValueError(f"{path}: competitor names are not unique")
    return competitors


def load_market_snippets(path: Path) -> dict[str, MarketSnippet]:
    records = json.loads(path.read_text(encoding="utf-8"))
    snippets = {}
    for position, record in enumerate(records, start=1):
        snippet = MarketSnippet(
            id=f"S{position:02d}",
            claim=record["claim"].strip(),
            stat=record["stat"].strip(),
            source_name=record["source_name"].strip() or None,
            source_url=record["source_url"].strip() or None,
            year=int(record["year"]) if record["year"].strip() else None,
        )
        snippets[snippet.id] = snippet
    return snippets
