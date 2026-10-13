"""LLM judge for the trap checklist and the 1-5 criteria, with its claims verified.

- Blind: the judge sees only the brief, never which system wrote it.
- Grounded: a trap counts as handled only if the judge's excerpt is found word for word in
  the brief. An LLM judge can claim things a brief never says; this catches it.
- Vetoed: where the deterministic citation check can see a trap (P06 cited as evidence,
  unusable snippets cited without a caveat), a failed check overrides the judge.
- Cached: verdicts are stored by a hash of the judge prompt, judge model and brief text,
  so re-running the evaluation is free and reproducible.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from discovery_chef.citations import CitationReport, normalise
from discovery_chef.eval.collect import BriefRecord
from discovery_chef.eval.rubric import CRITERIA, TRAPS, JudgeVerdict, judge_prompt
from discovery_chef.llm import Conversation, LLMClient

JUDGE_MODEL = "gemini-3.1-pro-preview"


@dataclass
class Judgement:
    brief_id: str
    traps: dict[str, bool]  # final verdict per trap
    criteria: dict[str, int | None]
    trap_notes: list[dict] = field(default_factory=list)
    justifications: dict[str, str] = field(default_factory=dict)

    @property
    def trap_rate(self) -> float:
        return round(sum(self.traps.values()) / len(self.traps), 3)

    @property
    def mean_criteria(self) -> float | None:
        scores = [s for s in self.criteria.values() if s is not None]
        return round(sum(scores) / len(scores), 3) if scores else None


def cache_key(markdown: str, model: str) -> str:
    return hashlib.sha256(f"{judge_prompt()}\n{model}\n{markdown}".encode()).hexdigest()[:16]


def judge(llm: LLMClient | None, record: BriefRecord, report: CitationReport,
          cache_dir: Path, *, model: str) -> Judgement | None:
    """Judge a brief with `model`, from the cache when possible.

    Without `llm`, only cached verdicts by that same judge model are used.
    """
    if llm is not None and llm.config.model != model:
        raise ValueError(f"judge client uses {llm.config.model}, expected {model}")
    path = cache_dir / f"{cache_key(record.markdown, model)}.json"
    if path.exists():
        verdict = JudgeVerdict.model_validate(json.loads(path.read_text())["verdict"])
    elif llm is None:
        return None
    else:
        conversation = Conversation(system=judge_prompt()).say(
            f"<brief>\n{record.markdown}\n</brief>\n\nGrade this brief.")
        verdict = llm.run(agent="judge", step=record.brief_id, conversation=conversation,
                          output_type=JudgeVerdict)
        cache_dir.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"brief_id": record.brief_id, "judge_model": model,
                                    "verdict": verdict.model_dump(mode="json")},
                                   indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return assess(record.brief_id, verdict, record.markdown, report)


def excerpt_in_brief(excerpt: str, markdown: str) -> bool:
    brief = normalise(markdown)
    parts = [p.strip(" .,;:!?\"'") for p in re.split(r"\.\.\.|…", normalise(excerpt))]
    parts = [p for p in parts if len(p) >= 8]
    return bool(parts) and all(p in brief for p in parts)


def assess(brief_id: str, verdict: JudgeVerdict, markdown: str,
           report: CitationReport) -> Judgement:
    by_trap = {a.trap_id: a for a in verdict.traps}
    vetoes = {
        "T01": "P06 cited as evidence" if report.excluded_citations else None,
        "T11": "unusable snippet cited without a caveat"
        if report.weak_snippet_citations else None,
    }
    traps, notes = {}, []
    for trap in TRAPS:
        assessment = by_trap.get(trap.id)
        claimed = bool(assessment and assessment.handled)
        verified = claimed and excerpt_in_brief(assessment.excerpt, markdown)
        veto = vetoes.get(trap.id)
        traps[trap.id] = verified and not veto
        notes.append({"trap_id": trap.id, "judge_says_handled": claimed,
                      "excerpt_verified": verified, "veto": veto,
                      "excerpt": assessment.excerpt if assessment else ""})

    scores = {c.criterion_id: c for c in verdict.criteria}
    criteria, justifications = {}, {}
    for criterion in CRITERIA:
        score = scores.get(criterion.id)
        criteria[criterion.id] = min(5, max(1, score.score)) if score else None
        justifications[criterion.id] = score.justification if score else ""
    return Judgement(brief_id=brief_id, traps=traps, criteria=criteria, trap_notes=notes,
                     justifications=justifications)
