"""Score every brief, compare the conditions, and write outputs/eval/.

Outputs
    scores.csv         one row per brief: automatic checks, traps, criteria, cost, latency
    summary.csv        one row per condition (means, plus ranges for the key numbers)
    traps.csv          share of briefs handling each trap, per condition
    objections.csv     every critic objection in every run with a critic
    loops.csv          each such run's critic loop: outcome and objections per round
    agreement.csv      judge versus human scores (when blind/human_scores.csv is filled in)
    judgements.json    per brief: the judge's weaknesses, verified misrepresentations, reasons
    eval_report.md     all of the above as readable tables
    figures/quality_vs_cost.png
    blind/             briefs under neutral IDs for hand-scoring, plus a scoring template
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from discovery_chef.citations import check_brief
from discovery_chef.context import DiscoveryContext
from discovery_chef.eval.collect import CONDITION_LABELS, CONDITIONS, BriefRecord, Skipped
from discovery_chef.eval.judge import Judgement, judge, source_pack
from discovery_chef.eval.rubric import CRITERIA, TRAPS, quality_index

HUMAN_SCORES = "human_scores.csv"
REVIEWED = ("informed_critic", "agents")  # conditions whose runs went through the critic


@dataclass
class EvalResult:
    scores: pd.DataFrame
    summary: pd.DataFrame
    traps: pd.DataFrame
    objections: pd.DataFrame
    loops: pd.DataFrame
    agreement: pd.DataFrame | None
    written: list[Path]


def evaluate(records: list[BriefRecord], ctx: DiscoveryContext, runs_dir: Path, out_dir: Path,
             *, judge_llm, judge_model: str, cache_dir: Path, skipped: list[Skipped],
             setup: dict) -> EvalResult:
    rows, judgements = [], {}
    sources = source_pack(ctx)
    for record in records:
        report = check_brief(record.markdown, ctx)
        judgement = judge(judge_llm, record, report, cache_dir, model=judge_model,
                          sources=sources)
        judgements[record.brief_id] = (record.condition, judgement)
        rows.append(_score_row(record, report, judgement))
    scores = pd.DataFrame(rows)
    if not scores.empty:
        scores["condition"] = pd.Categorical(scores["condition"], CONDITIONS, ordered=True)
        scores = scores.sort_values(["condition", "run_id"]).reset_index(drop=True)

    summary = _summary(scores)
    traps = _trap_table(scores)
    objections, loops = _critic_tables(runs_dir, sorted({(r.run_id, r.condition)
                                                          for r in records
                                                          if r.condition in REVIEWED}))
    out_dir.mkdir(parents=True, exist_ok=True)
    blind_dir = out_dir / "blind"
    _write_blind_kit(records, blind_dir)
    agreement = _agreement(scores, blind_dir)

    written = []
    tables = {"scores": scores, "summary": summary, "traps": traps,
              "objections": objections, "loops": loops}
    if agreement is not None:
        tables["agreement"] = agreement
    for name, df in tables.items():
        path = out_dir / f"{name}.csv"
        df.to_csv(path, index=False, lineterminator="\n")
        written.append(path)
    details_path = out_dir / "judgements.json"
    details_path.write_text(json.dumps({
        brief_id: {"condition": condition, "weaknesses": j.weaknesses,
                   "misrepresentations": j.misrepresentations,
                   "criteria_reasons": j.justifications,
                   "traps_missed": [t for t, ok in j.traps.items() if not ok]}
        for brief_id, (condition, j) in sorted(judgements.items()) if j is not None
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    written.append(details_path)
    report_path = out_dir / "eval_report.md"
    report_path.write_text(_markdown(scores, summary, traps, objections, loops, agreement,
                                     skipped, setup), encoding="utf-8")
    written.append(report_path)
    if not scores.empty and scores["quality_index"].notna().any():
        from discovery_chef.eval.charts import quality_vs_cost

        figure_dir = out_dir / "figures"
        figure_dir.mkdir(exist_ok=True)
        path = figure_dir / "quality_vs_cost.png"
        quality_vs_cost(scores).savefig(path, dpi=150, metadata={"Software": None})
        written.append(path)
    return EvalResult(scores, summary, traps, objections, loops, agreement, written)


def _score_row(record: BriefRecord, report, judgement: Judgement | None) -> dict:
    row = {
        "brief_id": record.brief_id,
        "condition": record.condition,
        "run_id": record.run_id,
        "recommendation": record.recommendation,
        "blocking_issues": report.blocking,
        "citations": report.citations,
        "distinct_sources": report.distinct_sources,
        "coverage": report.coverage,
        "verified_quotes": report.verified_quotes,
        "unverified_numbers": len(report.unverified_numbers),
        "uncited_claims": len(report.uncited_claims),
        "cost_usd": record.cost_usd,
        "wall_clock_s": record.wall_clock_s,
        "calls": record.calls,
        "judged": judgement is not None,
    }
    for trap in TRAPS:
        row[trap.id] = judgement.traps[trap.id] if judgement else None
    for criterion in CRITERIA:
        row[criterion.id] = judgement.criteria[criterion.id] if judgement else None
    row["trap_rate"] = judgement.trap_rate if judgement else None
    row["mean_criteria"] = judgement.mean_criteria if judgement else None
    row["misrepresentations"] = len(judgement.misrepresentations) if judgement else None
    row["faithfulness"] = judgement.faithfulness if judgement else None
    row["unverified_judge_claims"] = judgement.unverified_claims if judgement else None
    row["quality_index"] = (
        quality_index(judgement.trap_rate, judgement.mean_criteria, judgement.faithfulness)
        if judgement and judgement.mean_criteria is not None else None)
    return row


SUMMARY_COLUMNS = ("quality_index", "trap_rate", "misrepresentations", "faithfulness",
                   "mean_criteria", *(c.id for c in CRITERIA),
                   "blocking_issues", "coverage", "verified_quotes", "unverified_numbers",
                   "cost_usd", "wall_clock_s", "calls")


def _summary(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for condition in CONDITIONS:
        group = scores[scores["condition"] == condition] if not scores.empty else scores
        if group.empty:
            continue
        row = {"condition": condition, "label": CONDITION_LABELS[condition], "n": len(group)}
        for column in SUMMARY_COLUMNS:
            values = pd.to_numeric(group[column], errors="coerce")
            row[column] = round(values.mean(), 4) if values.notna().any() else None
        for column in ("quality_index", "cost_usd", "wall_clock_s"):
            values = pd.to_numeric(group[column], errors="coerce").dropna()
            row[f"{column}_min"] = round(values.min(), 4) if len(values) else None
            row[f"{column}_max"] = round(values.max(), 4) if len(values) else None
        row["recommendations"] = "; ".join(
            f"{name} x{count}" for name, count in group["recommendation"].value_counts().items())
        rows.append(row)
    return pd.DataFrame(rows)


def _trap_table(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for trap in TRAPS:
        row = {"trap": trap.id, "name": trap.name, "eda_finding": trap.finding}
        for condition in CONDITIONS:
            group = scores[(scores["condition"] == condition) & scores["judged"]] \
                if not scores.empty else scores
            row[condition] = round(group[trap.id].astype(float).mean(), 3) \
                if len(group) else None
        rows.append(row)
    return pd.DataFrame(rows)


def _critic_tables(runs_dir: Path, runs: list[tuple[str, str]]
                   ) -> tuple[pd.DataFrame, pd.DataFrame]:
    objection_rows, loop_rows = [], []
    for run_id, system in runs:
        run = json.loads((runs_dir / run_id / "run.json").read_text(encoding="utf-8"))
        for round_info in run["rounds"]:
            number = round_info["round"]
            critique_path = runs_dir / run_id / "review" / f"round-{number}" / "critique.json"
            critique = json.loads(critique_path.read_text(encoding="utf-8"))
            for objection in critique["objections"]:
                objection_rows.append({"run_id": run_id, "system": system, "round": number,
                                       "severity": objection["severity"],
                                       "category": objection["category"],
                                       "section": objection["section"],
                                       "problem": objection["problem"]})
            loop_rows.append({
                "run_id": run_id, "system": system, "round": number,
                "verdict": round_info["verdict"],
                "blockers": round_info["blockers"], "majors": round_info["majors"],
                "minors": round_info["minors"],
                "check_blocking": round_info["citation_check"]["blocking"],
                "loop_outcome": run["loop_outcome"],
            })
    return (pd.DataFrame(objection_rows, columns=["run_id", "system", "round", "severity",
                                                  "category", "section", "problem"]),
            pd.DataFrame(loop_rows, columns=["run_id", "system", "round", "verdict", "blockers",
                                             "majors", "minors", "check_blocking",
                                             "loop_outcome"]))


# --- blind hand-scoring ----------------------------------------------------------------------

def blind_id(brief_id: str) -> str:
    """Neutral, stable ID: adding runs later never renames a brief you already scored."""
    return "B" + hashlib.sha256(brief_id.encode()).hexdigest()[:6]


def _write_blind_kit(records: list[BriefRecord], blind_dir: Path) -> None:
    blind_dir.mkdir(parents=True, exist_ok=True)
    for old in blind_dir.glob("B*.md"):
        old.unlink()
    ids = {r.brief_id: blind_id(r.brief_id) for r in records}
    for record in records:
        (blind_dir / f"{ids[record.brief_id]}.md").write_text(record.markdown, encoding="utf-8")
    (blind_dir / "key.json").write_text(json.dumps(
        {blind: brief_id for brief_id, blind in sorted(ids.items(), key=lambda kv: kv[1])},
        indent=2) + "\n", encoding="utf-8")
    header = ["blind_id", *(c.id for c in CRITERIA), "notes"]
    with (blind_dir / "human_scores_template.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        for blind in sorted(ids.values()):
            writer.writerow([blind, *[""] * len(CRITERIA), ""])
    guide = ["# Hand-scoring guide", "",
             "Score a few of the B*.md briefs without opening key.json. Copy",
             f"human_scores_template.csv to {HUMAN_SCORES}, fill in 1-5 per criterion for the",
             "briefs you read, leave the rest empty, then run `uv run discovery-chef evaluate`.",
             ""]
    for c in CRITERIA:
        guide += [f"## {c.id} {c.name}", c.question, "",
                  f"- 1: {c.anchors[0]}", f"- 3: {c.anchors[1]}", f"- 5: {c.anchors[2]}", ""]
    (blind_dir / "README.md").write_text("\n".join(guide), encoding="utf-8")


def _agreement(scores: pd.DataFrame, blind_dir: Path) -> pd.DataFrame | None:
    path = blind_dir / HUMAN_SCORES
    if not path.exists() or scores.empty:
        return None
    key = json.loads((blind_dir / "key.json").read_text(encoding="utf-8"))
    human = pd.read_csv(path)
    human["brief_id"] = human["blind_id"].map(key)
    merged = human.merge(scores, on="brief_id", suffixes=("_human", "_judge"))
    rows = []
    for c in CRITERIA:
        pairs = merged[[f"{c.id}_human", f"{c.id}_judge"]].apply(pd.to_numeric,
                                                                 errors="coerce").dropna()
        if pairs.empty:
            continue
        diff = (pairs[f"{c.id}_human"] - pairs[f"{c.id}_judge"]).abs()
        rows.append({"criterion": c.id, "name": c.name, "briefs": len(pairs),
                     "mean_abs_difference": round(diff.mean(), 3),
                     "exact_agreement": round((diff == 0).mean(), 3),
                     "within_one": round((diff <= 1).mean(), 3)})
    return pd.DataFrame(rows) if rows else None


# --- markdown report -------------------------------------------------------------------------

def _fmt(value, kind: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    if kind == "usd":
        return f"${value:.3f}"
    if kind == "pct":
        return f"{value:.0%}"
    if kind == "s":
        return f"{value:.0f}s"
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else f"{value:.2f}"
    return str(value)


def _with_range(row, column: str) -> str:
    mean, low, high = row[column], row[f"{column}_min"], row[f"{column}_max"]
    if low is None or pd.isna(low) or low == high:
        return _fmt(mean)
    return f"{_fmt(mean)} ({_fmt(low)}-{_fmt(high)})"


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header),
            *["| " + " | ".join(row) + " |" for row in rows]]


def _markdown(scores, summary, traps, objections, loops, agreement, skipped, setup) -> str:
    out = ["# Evaluation: multi-agent versus single prompt", "",
           "Generated by `uv run discovery-chef evaluate`. Do not edit by hand.", ""]
    out += [f"- {key}: {value}" for key, value in setup.items()]
    other = [s for s in skipped if not s.failed]
    out += [f"- runs left out as not comparable: {len(other)} "
            f"({'; '.join(sorted({s.reason for s in other})) or 'none'})", ""]
    failed = [s for s in skipped if s.failed]
    if failed:
        out += ["## Runs that failed", "",
                "Comparable runs (same model and code) that crashed. They count against "
                "reliability and their cost was still spent.", ""]
        out += _table(["Run", "System", "Spent", "Error"],
                      [[s.run_id, s.system or "-", _fmt(s.cost_usd, "usd"), s.reason[:140]]
                       for s in failed])
        out += [""]
    if summary.empty:
        return "\n".join(out + ["No comparable runs found.", ""])

    by = summary.set_index("condition")
    present = list(by.index)
    out += ["## Overview", ""]
    out += _table(
        ["", *(CONDITION_LABELS[c] for c in present)],
        [["Briefs", *(str(int(by.loc[c, "n"])) for c in present)],
         ["Runs failed", *(_failures(failed, c) for c in present)],
         ["Quality index (0-1)", *(_with_range(by.loc[c], "quality_index") for c in present)],
         ["Traps handled", *(_fmt(by.loc[c, "trap_rate"], "pct") for c in present)],
         ["Sources misrepresented (per brief)",
          *(_fmt(by.loc[c, "misrepresentations"]) for c in present)],
         ["Mean criterion score (1-5)", *(_fmt(by.loc[c, "mean_criteria"]) for c in present)],
         ["Blocking citation issues", *(_fmt(by.loc[c, "blocking_issues"]) for c in present)],
         ["Claim lines cited", *(_fmt(by.loc[c, "coverage"], "pct") for c in present)],
         ["Quotes verified", *(_fmt(by.loc[c, "verified_quotes"]) for c in present)],
         ["Cost per brief", *(_fmt(by.loc[c, "cost_usd"], "usd") for c in present)],
         ["Wall clock", *(_fmt(by.loc[c, "wall_clock_s"], "s") for c in present)],
         ["API calls", *(_fmt(by.loc[c, "calls"]) for c in present)],
         ["Recommendations", *(str(by.loc[c, "recommendations"]) for c in present)]])
    out += ["", "Quality index = the mean of three 0-1 scores: traps handled, faithfulness "
            "(1 minus 0.25 per verified misrepresentation) and the mean criterion score "
            "rescaled from 1-5. Values are means; ranges in brackets.", ""]

    steps = [("informed", "naive", "Adding the EDA's rules (one call)"),
             ("informed_critic", "informed", "A critic on the single prompt"),
             ("agents_draft", "informed", "Splitting the work across agents"),
             ("agents", "agents_draft", "A critic on the agents")]
    step_rows = []
    for after, before, label in steps:
        if after in by.index and before in by.index:
            step_rows.append([
                label,
                _signed(by.loc[after, "quality_index"], by.loc[before, "quality_index"]),
                _signed(by.loc[after, "trap_rate"], by.loc[before, "trap_rate"], pct=True),
                _signed(by.loc[after, "misrepresentations"],
                        by.loc[before, "misrepresentations"]),
                _signed(by.loc[after, "mean_criteria"], by.loc[before, "mean_criteria"]),
                _signed(by.loc[after, "cost_usd"], by.loc[before, "cost_usd"], usd=True),
                _signed(by.loc[after, "wall_clock_s"], by.loc[before, "wall_clock_s"], sec=True),
            ])
    if step_rows:
        out += ["## What each step adds", ""]
        out += _table(["Step", "Quality index", "Traps", "Misrepresentations", "Criteria",
                       "Cost", "Time"], step_rows)
        out += [""]

    out += ["## Criteria (mean, 1-5)", ""]
    out += _table(["Criterion", *(CONDITION_LABELS[c] for c in present)],
                  [[f"{c.id} {c.name}", *(_fmt(by.loc[k, c.id]) for k in present)]
                   for c in CRITERIA])
    out += ["", "## Traps (share of briefs handling each)", ""]
    out += _table(["Trap", "EDA", *(CONDITION_LABELS[c] for c in present)],
                  [[f"{r['trap']} {r['name']}", r["eda_finding"],
                    *(_fmt(r[c], "pct") for c in present)] for _, r in traps.iterrows()])

    if not loops.empty:
        out += ["", "## The critic loop", ""]
        for system in REVIEWED:
            out += _loop_section(loops[loops["system"] == system],
                                 objections[objections["system"] == system], system)
    if agreement is not None:
        out += ["", "## Judge versus human", ""]
        out += _table(["Criterion", "Briefs", "Mean abs. difference", "Exact", "Within 1"],
                      [[f"{r['criterion']} {r['name']}", str(r["briefs"]),
                        _fmt(r["mean_abs_difference"]), _fmt(r["exact_agreement"], "pct"),
                        _fmt(r["within_one"], "pct")] for _, r in agreement.iterrows()])
    out += ["", "## Caveats", "",
            "- Few runs per condition: differences smaller than the ranges above may be noise.",
            "- The judge is a Gemini model grading Gemini output; it may favour its own style. "
            "Trap and misrepresentation verdicts are grounded in verified excerpts (the "
            "judge's claim is dropped when its excerpt is not in the brief); criterion scores "
            "are not, so check them against the human scores.",
            "- A misrepresentation the judge misses is not counted; faithfulness is an upper "
            "bound.",
            "- The data is synthetic and fixed; results describe this case, not discovery work "
            "in general.", ""]
    return "\n".join(out)


def _loop_section(loops: pd.DataFrame, objections: pd.DataFrame, system: str) -> list[str]:
    if loops.empty:
        return []
    outcomes = loops.drop_duplicates("run_id")["loop_outcome"].value_counts()
    rounds = loops.groupby("run_id")["round"].max().add(1)
    severities = objections["severity"].value_counts()
    out = [f"### {CONDITION_LABELS[system]}", "",
           f"- Outcomes: {', '.join(f'{k} x{v}' for k, v in outcomes.items())}",
           f"- Review rounds per run: {', '.join(str(int(r)) for r in rounds)}",
           f"- Objections raised: {len(objections)} "
           f"({', '.join(f'{k} {v}' for k, v in severities.items()) or 'none'})", ""]
    if len(objections):
        counts = objections.groupby(["category", "severity"]).size().unstack(fill_value=0)
        out += _table(["Category", *counts.columns],
                      [[category, *(str(v) for v in row)] for category, row in counts.iterrows()])
        out += [""]
    return out


def _failures(failed: list[Skipped], condition: str) -> str:
    system = "agents" if condition.startswith("agents") else condition
    return str(sum(s.system == system for s in failed))


def _signed(after, before, *, pct=False, usd=False, sec=False) -> str:
    if after is None or before is None or pd.isna(after) or pd.isna(before):
        return "-"
    delta = after - before
    if pct:
        return f"{delta * 100:+.0f} pts"
    if usd:
        return f"{'+' if delta >= 0 else '-'}${abs(delta):.3f}"
    if sec:
        return f"{delta:+.0f}s"
    return f"{delta:+.2f}"
