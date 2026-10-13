"""Build the EDA evidence profile and write it to `outputs/eda/`.

`evidence_profile.json` is the hand-off contract to Phase 2: the agents read interview
weights, source reliability and the "So the agent will ..." rules from it instead of
re-deriving them.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from discovery_chef.dataset import Dataset, load_dataset
from discovery_chef.eda import interviews, sources
from discovery_chef.eda.annotations import (
    EVIDENCE_TIERS,
    FIT_FACTOR,
    INTERVIEW_CODING,
    LEADING_EXCLUSION_THRESHOLD,
    QUALITY_PENALTY,
)
from discovery_chef.eda.codebook import INJECTION_PATTERN
from discovery_chef.eda.findings import QUESTIONS, Finding, build_findings
from discovery_chef.paths import DATA_DIR, EDA_OUTPUT_DIR

SCHEMA_VERSION = 1


@dataclass
class EdaProfile:
    dataset: Dataset
    data_sha256: dict[str, str]
    metrics: pd.DataFrame
    coding: pd.DataFrame
    shared_sentences: pd.DataFrame
    theme_hits: pd.DataFrame
    theme_support: pd.DataFrame
    theme_matrix: pd.DataFrame
    competitors: pd.DataFrame
    capabilities: pd.DataFrame
    snippets: pd.DataFrame
    injection_hits: list[dict]
    findings: list[Finding] = field(default_factory=list)

    def findings_for(self, question: str) -> list[Finding]:
        return [f for f in self.findings if f.question == question]


def build_profile(data_dir: Path = DATA_DIR) -> EdaProfile:
    dataset = load_dataset(data_dir)
    shared = interviews.shared_sentences(dataset.interviews)
    metrics = interviews.interview_metrics(dataset.interviews, shared)
    hits = interviews.theme_hits(dataset.interviews, shared)
    profile = EdaProfile(
        dataset=dataset,
        data_sha256=data_checksums(data_dir),
        metrics=metrics,
        coding=interviews.coding_table(),
        shared_sentences=shared,
        theme_hits=hits,
        theme_support=interviews.theme_support(hits, metrics),
        theme_matrix=interviews.theme_matrix(hits, dataset.interviews),
        competitors=sources.competitor_profile(dataset.competitors, dataset.as_of),
        capabilities=sources.capability_matrix(dataset.competitors),
        snippets=sources.snippet_profile(dataset.snippets, dataset.as_of),
        injection_hits=scan_for_instructions(data_dir),
    )
    profile.findings = build_findings(profile)
    return profile


def data_checksums(data_dir: Path = DATA_DIR) -> dict[str, str]:
    return {
        path.relative_to(data_dir).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(data_dir.rglob("*"))
        if path.is_file()
    }


def scan_for_instructions(data_dir: Path = DATA_DIR) -> list[dict]:
    hits = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if INJECTION_PATTERN.search(line):
                hits.append({"file": path.relative_to(data_dir).as_posix(), "line": number,
                             "text": line.strip()})
    return hits


# --- serialisation -------------------------------------------------------------------------

def _records(df: pd.DataFrame) -> list[dict]:
    clean = df.astype(object).where(df.notna(), None)
    return clean.to_dict("records")


def to_json_dict(p: EdaProfile) -> dict:
    metrics = p.metrics.set_index("interview_id")
    interviews_out = {}
    for iid, coding in INTERVIEW_CODING.items():
        row = metrics.loc[iid]
        interviews_out[iid] = {
            "persona": p.dataset.interviews[iid].persona,
            "date": row["date"],
            "household_type": coding.household_type,
            "household_size": coding.household_size,
            "target_fit": coding.target_fit,
            "fit_rationale": coding.fit_rationale,
            "evidence_quality": float(row["evidence_quality"]),
            "evidence_weight": float(row["evidence_weight"]),
            "evidence_tier": row["evidence_tier"],
            "shopping_pattern": coding.shopping_pattern,
            "current_tools": coding.current_tools,
            "wtp": {
                "category": coding.wtp.category,
                "max_eur_per_month": coding.wtp.max_eur_per_month,
                "quote": coding.wtp.quote,
            },
            "issues": [
                {"kind": i.kind, "severity": i.severity, "scope": i.scope, "note": i.note,
                 "quotes": list(i.quotes)}
                for i in coding.issues
            ],
            "themes": sorted(p.theme_hits.loc[p.theme_hits["interview_id"] == iid, "theme"]
                             .unique().tolist()),
            "metrics": {
                k: row[k] for k in (
                    "participant_words", "off_guide_questions", "leading_questions",
                    "acquiescent_answers", "templated_sentence_ratio",
                )
            },
        }

    competitors_out = {}
    for record in _records(p.competitors):
        caps = p.capabilities.loc[record["competitor"]]
        competitors_out[record["competitor"]] = {
            **record, "capabilities": [k for k, v in caps.items() if v],
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "as_of": p.dataset.as_of.isoformat(),
        "target_customer": p.dataset.idea.target_customer,
        "data_sha256": p.data_sha256,
        "citation_ids": {
            "interviews": sorted(p.dataset.interviews),
            "competitors": sorted(p.dataset.competitors),
            "market_snippets": sorted(p.dataset.snippets),
        },
        "weighting_rule": {
            "formula": "evidence_weight = evidence_quality x fit_factor",
            "quality_penalty_per_interview_issue": QUALITY_PENALTY,
            "fit_factor": FIT_FACTOR,
            "leading_exclusion_threshold": LEADING_EXCLUSION_THRESHOLD,
            "tiers": [{"min_weight": w, "tier": t} for w, t in EVIDENCE_TIERS],
        },
        "interviews": interviews_out,
        "templated_sentences": _records(p.shared_sentences),
        "themes": _records(p.theme_support),
        "competitors": competitors_out,
        "market_snippets": {r["snippet_id"]: r for r in _records(p.snippets)},
        "injection_scan": {"pattern": INJECTION_PATTERN.pattern, "hits": p.injection_hits},
        "questions": QUESTIONS,
        "findings": [f.to_dict() for f in p.findings],
    }


def findings_markdown(findings: list[Finding], *, heading_level: int = 3) -> str:
    hashes = "#" * heading_level
    blocks = []
    for f in findings:
        evidence = ", ".join(f.evidence) if f.evidence else "whole dataset"
        star = " ★" if f.headline else ""
        blocks.append(
            f"{hashes} {f.id}{star} - {f.title}\n\n{f.finding}\n\n"
            f"*Evidence: {evidence}*\n\n**{f.so_the_agent_will}**"
        )
    return "\n\n".join(blocks)


def findings_report(p: EdaProfile) -> str:
    parts = [
        "# EDA findings",
        "",
        "Generated by `uv run discovery-chef eda` from the files in `data/` "
        f"(research date {p.dataset.as_of.isoformat()}). Do not edit by hand.",
        "",
        "★ marks the findings that matter most for the brief.",
    ]
    for qid, question in QUESTIONS.items():
        parts += ["", f"## {qid}. {question}", "", findings_markdown(p.findings_for(qid))]
    return "\n".join(parts) + "\n"


def _csv_ready(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in out.columns:
        if out[column].map(lambda v: isinstance(v, (list, tuple))).any():
            out[column] = out[column].map(
                lambda v: "; ".join(map(str, v)) if isinstance(v, (list, tuple)) else v
            )
    return out


def write_outputs(p: EdaProfile, out_dir: Path = EDA_OUTPUT_DIR, *,
                  figures: bool = True) -> list[Path]:
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    written = []

    profile_path = out_dir / "evidence_profile.json"
    profile_path.write_text(
        json.dumps(to_json_dict(p), indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )
    written.append(profile_path)

    report_path = out_dir / "findings.md"
    report_path.write_text(findings_report(p), encoding="utf-8")
    written.append(report_path)

    tables = {
        "interviews": p.metrics,
        "interview_coding": p.coding,
        "templated_sentences": p.shared_sentences,
        "theme_hits": p.theme_hits,
        "theme_support": p.theme_support,
        "theme_matrix": p.theme_matrix.reset_index(),
        "competitors": p.competitors,
        "competitor_capabilities": p.capabilities.rename_axis("competitor").reset_index(),
        "market_snippets": p.snippets,
    }
    for name, df in tables.items():
        path = tables_dir / f"{name}.csv"
        _csv_ready(df).to_csv(path, index=False, lineterminator="\n")
        written.append(path)

    if figures:
        from discovery_chef.eda import charts

        written += charts.save_all(p, out_dir / "figures")
    return written


def _json_default(value):
    if hasattr(value, "item"):  # numpy scalars
        return value.item()
    raise TypeError(f"Not JSON serialisable: {type(value).__name__}")


def run_eda(out_dir: Path = EDA_OUTPUT_DIR, *, figures: bool = True) -> EdaProfile:
    profile = build_profile()
    write_outputs(profile, out_dir, figures=figures)
    return profile
