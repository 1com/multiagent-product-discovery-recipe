"""Computed interview metrics: guide adherence, leading questions, templated answers,
evidence weights and theme coding."""

from __future__ import annotations

from collections import Counter, defaultdict

import pandas as pd

from discovery_chef.dataset import Interview
from discovery_chef.eda.annotations import (
    EVIDENCE_TIERS,
    FIT_FACTOR,
    INTERVIEW_CODING,
    LEADING_EXCLUSION_THRESHOLD,
    QUALITY_PENALTY,
)
from discovery_chef.eda.codebook import (
    ACQUIESCENT_PATTERN,
    LEADING_PATTERNS,
    PRESUPPOSING_PATTERN,
    THEMES,
)

# Sentences shorter than this ("Just me.", "Not really.") coincide naturally across people.
MIN_TEMPLATE_WORDS = 4


def normalise(sentence: str) -> str:
    return " ".join(sentence.lower().split())


def interview_guide(interviews: dict[str, Interview]) -> dict[int, str]:
    """The modal question asked at each turn: the shared interview guide."""
    by_turn: dict[int, Counter[str]] = defaultdict(Counter)
    for interview in interviews.values():
        for turn in interview.turns:
            by_turn[turn.number][turn.question] += 1
    return {number: counts.most_common(1)[0][0] for number, counts in sorted(by_turn.items())}


def leading_flags(question: str) -> list[str]:
    return [name for name, pattern in LEADING_PATTERNS.items() if pattern.search(question)]


def shared_sentences(interviews: dict[str, Interview]) -> pd.DataFrame:
    """Answer sentences that appear word for word in more than one interview."""
    where: dict[str, set[str]] = defaultdict(set)
    original: dict[str, str] = {}
    for interview in interviews.values():
        for turn in interview.turns:
            for sentence in turn.answer_sentences:
                if len(sentence.split()) < MIN_TEMPLATE_WORDS:
                    continue
                key = normalise(sentence)
                where[key].add(interview.id)
                original.setdefault(key, sentence)
    rows = [
        {"sentence": original[key], "n_interviews": len(ids), "interviews": sorted(ids)}
        for key, ids in where.items()
        if len(ids) > 1
    ]
    return (
        pd.DataFrame(rows, columns=["sentence", "n_interviews", "interviews"])
        .sort_values(["n_interviews", "sentence"], ascending=[False, True])
        .reset_index(drop=True)
    )


def interview_metrics(interviews: dict[str, Interview], shared: pd.DataFrame) -> pd.DataFrame:
    guide = interview_guide(interviews)
    templated = {normalise(s) for s in shared["sentence"]}
    rows = []
    for interview in interviews.values():
        coding = INTERVIEW_CODING[interview.id]
        turns = interview.turns
        sentences = [s for t in turns for s in t.answer_sentences
                     if len(s.split()) >= MIN_TEMPLATE_WORDS]
        leading = [t.number for t in turns if leading_flags(t.question)]
        weight_issues = interview_scoped(coding.issues)
        row = {
            "interview_id": interview.id,
            "date": interview.date.isoformat(),
            "persona": interview.persona,
            "household_type": coding.household_type,
            "household_size": coding.household_size,
            "cooks_most_weeknights": coding.cooks_most_weeknights,
            "target_fit": coding.target_fit,
            "participant_words": interview.participant_words,
            "off_guide_questions": sum(t.question != guide[t.number] for t in turns),
            "leading_questions": len(leading),
            "leading_question_ratio": round(len(leading) / len(turns), 2),
            "presupposing_questions": sum(bool(PRESUPPOSING_PATTERN.search(t.question))
                                          for t in turns),
            "acquiescent_answers": sum(bool(ACQUIESCENT_PATTERN.search(t.answer))
                                       for t in turns),
            "templated_sentence_ratio": round(
                sum(normalise(s) in templated for s in sentences) / len(sentences), 2
            ),
            # Issues that lower the evidence weight (scope "interview") ...
            "major_issues": sum(i.severity == "major" for i in weight_issues),
            "minor_issues": sum(i.severity == "minor" for i in weight_issues),
            # ... and issues that only caveat one topic (e.g. P08's willingness to pay).
            "topic_caveats": len(coding.issues) - len(weight_issues),
        }
        row.update(_evidence_weight(row, coding))
        rows.append(row)
    return pd.DataFrame(rows)


def interview_scoped(issues) -> list:
    """The issues that undermine a whole interview, and so lower its evidence weight."""
    return [i for i in issues if i.scope == "interview"]


def _evidence_weight(row: dict, coding) -> dict:
    """Quality (1.0 minus issue penalties) times target fit; see annotations.py."""
    if row["leading_question_ratio"] >= LEADING_EXCLUSION_THRESHOLD:
        quality = 0.0
    else:
        penalty = sum(QUALITY_PENALTY[i.severity] for i in interview_scoped(coding.issues))
        quality = max(0.0, 1.0 - penalty)
    weight = round(quality * FIT_FACTOR[coding.target_fit], 2)
    tier = next(name for minimum, name in EVIDENCE_TIERS if weight >= minimum)
    return {"evidence_quality": round(quality, 2), "evidence_weight": weight,
            "evidence_tier": tier}


def theme_hits(interviews: dict[str, Interview], shared: pd.DataFrame) -> pd.DataFrame:
    """Every participant sentence matched by a codebook theme, with its location."""
    templated = {normalise(s) for s in shared["sentence"]}
    rows = []
    for interview in interviews.values():
        for turn in interview.turns:
            for sentence in turn.answer_sentences:
                for theme in THEMES:
                    if theme.matches(sentence):
                        rows.append({
                            "interview_id": interview.id,
                            "theme": theme.key,
                            "kind": theme.kind,
                            "turn": turn.number,
                            "sentence": sentence,
                            "templated": normalise(sentence) in templated,
                        })
    return pd.DataFrame(rows)


def theme_support(hits: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    """How many interviews back each theme: raw, evidence-weighted and non-templated."""
    weights = metrics.set_index("interview_id")["evidence_weight"]
    rows = []
    for theme in THEMES:
        theme_rows = hits[hits["theme"] == theme.key]
        ids = sorted(theme_rows["interview_id"].unique())
        own_words = sorted(theme_rows.loc[~theme_rows["templated"], "interview_id"].unique())
        rows.append({
            "theme": theme.key,
            "label": theme.label,
            "kind": theme.kind,
            "raw_interviews": len(ids),
            "weighted_support": round(float(sum(weights[i] for i in ids)), 2),
            "non_templated_interviews": len(own_words),
            "interviews": ids,
            "own_words_interviews": own_words,
            "excluded_interviews": [i for i in ids if weights[i] == 0],
        })
    return pd.DataFrame(rows).sort_values(
        ["kind", "weighted_support"], ascending=[True, False], key=_kind_order
    ).reset_index(drop=True)


def _kind_order(column: pd.Series) -> pd.Series:
    if column.name == "kind":
        return column.map({"problem": 0, "requirement": 1, "counter_evidence": 2})
    return column


def theme_matrix(hits: pd.DataFrame, interviews: dict[str, Interview]) -> pd.DataFrame:
    """Theme x interview grid: 1 where the interview mentions the theme."""
    order = [theme.key for theme in THEMES]
    grid = pd.crosstab(hits["theme"], hits["interview_id"]).clip(upper=1)
    return grid.reindex(index=order, columns=sorted(interviews), fill_value=0)


def coding_table() -> pd.DataFrame:
    """Analyst coding flattened for display: fit, shopping, tools, WTP, issues."""
    rows = []
    for coding in INTERVIEW_CODING.values():
        rows.append({
            "interview_id": coding.interview_id,
            "target_fit": coding.target_fit,
            "fit_rationale": coding.fit_rationale,
            "shopping_pattern": coding.shopping_pattern,
            "current_tools": coding.current_tools,
            "wtp_category": coding.wtp.category,
            "wtp_max_eur_month": coding.wtp.max_eur_per_month,
            "wtp_quote": coding.wtp.quote,
            "issues": "; ".join(f"[{i.severity}/{i.scope}] {i.kind}" for i in coding.issues),
        })
    return pd.DataFrame(rows)
