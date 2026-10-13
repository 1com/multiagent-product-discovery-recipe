"""Retrieval over the interviews, with citations down to the interview turn.

Each question-answer turn is one passage with ID `P02:t4` (interview P02, turn 4). Passages
carry the EDA's evidence metadata (tier, weight, target fit, templated sentences), so an
agent sees how far to trust a quote at the moment it reads it. Ranking is BM25 over the
answer plus the question that prompted it. It is deterministic and needs no API.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from discovery_chef.dataset import Dataset

STOPWORDS = frozenset("""
a about after again all also am an and any are as at be because been before being both but
by can could did do does doing for from had has have having he her here hers him his how i
if in into is it its just me more most my no nor not now of off on once only or other our
out over own same she should so some such than that the their them then there these they
this those through to too under until up very was we were what when where which while who
whom why will with would you your yours really maybe much well
""".split())

_TOKEN = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw in _TOKEN.findall(text.lower()):
        word = raw.strip("'")
        if word.endswith("'s"):
            word = word[:-2]
        if not word or word in STOPWORDS:
            continue
        tokens.append(_stem(word))
    return tokens


def _stem(word: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


@dataclass(frozen=True)
class Passage:
    id: str
    interview_id: str
    turn: int
    question: str
    answer: str
    evidence_tier: str
    evidence_weight: float
    target_fit: str
    household_type: str
    templated_sentences: tuple[str, ...]

    def render(self) -> str:
        templated = "; ".join(f'"{s}"' for s in self.templated_sentences) or "none"
        return (
            f'<source id="{self.id}" type="interview_turn" tier="{self.evidence_tier}" '
            f'weight="{self.evidence_weight:.2f}" target_fit="{self.target_fit}" '
            f'household="{self.household_type}">\n'
            f"Interviewer: {self.question}\n"
            f"Participant: {self.answer}\n"
            f"Sentences shared word for word with other interviews: {templated}\n"
            f"</source>"
        )


@dataclass(frozen=True)
class Hit:
    passage: Passage
    score: float


class InterviewIndex:
    """BM25 index over interview turns (k1=1.5, b=0.75)."""

    def __init__(self, passages: list[Passage], k1: float = 1.5, b: float = 0.75):
        self.passages = passages
        self.by_id = {p.id: p for p in passages}
        self._k1, self._b = k1, b
        self._docs = [Counter(tokenize(f"{p.question} {p.answer} {p.answer}"))
                      for p in passages]  # answer counted twice: it carries the evidence
        self._lengths = [sum(d.values()) for d in self._docs]
        self._avg_length = sum(self._lengths) / len(self._lengths)
        df = Counter(term for doc in self._docs for term in doc)
        n = len(passages)
        self._idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    @classmethod
    def build(cls, dataset: Dataset, profile: dict) -> InterviewIndex:
        templated = {}
        for row in profile["templated_sentences"]:
            for iid in row["interviews"]:
                templated.setdefault(iid, set()).add(" ".join(row["sentence"].lower().split()))
        passages = []
        for interview in dataset.interviews.values():
            meta = profile["interviews"][interview.id]
            shared = templated.get(interview.id, set())
            for turn in interview.turns:
                passages.append(Passage(
                    id=f"{interview.id}:t{turn.number}",
                    interview_id=interview.id,
                    turn=turn.number,
                    question=turn.question,
                    answer=turn.answer,
                    evidence_tier=meta["evidence_tier"],
                    evidence_weight=meta["evidence_weight"],
                    target_fit=meta["target_fit"],
                    household_type=meta["household_type"],
                    templated_sentences=tuple(
                        s for s in turn.answer_sentences
                        if " ".join(s.lower().split()) in shared
                    ),
                ))
        return cls(passages)

    def search(self, query: str, k: int = 6, *, include_excluded: bool = False,
               interview_ids: list[str] | None = None) -> list[Hit]:
        terms = tokenize(query)
        hits = []
        for passage, doc, length in zip(self.passages, self._docs, self._lengths, strict=True):
            if not include_excluded and passage.evidence_tier == "excluded":
                continue
            if interview_ids and passage.interview_id not in interview_ids:
                continue
            score = 0.0
            for term in terms:
                tf = doc.get(term, 0)
                if tf:
                    norm = tf + self._k1 * (1 - self._b + self._b * length / self._avg_length)
                    score += self._idf[term] * tf * (self._k1 + 1) / norm
            if score > 0:
                hits.append(Hit(passage, round(score, 4)))
        hits.sort(key=lambda h: (-h.score, h.passage.id))
        return hits[:k]

    def interview(self, interview_id: str) -> list[Passage]:
        return [p for p in self.passages if p.interview_id == interview_id]
