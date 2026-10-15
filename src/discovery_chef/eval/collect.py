"""Find comparable runs in outputs/runs/ and turn each into briefs to score.

Five conditions isolate what each part of the system adds:
    naive            single prompt, raw data                       (baseline)
    informed         single prompt + the EDA's rules               -> the EDA's effect
    informed_critic  informed, then the agents' critic loop        -> the critic, without agents
    agents_draft     multi-agent brief before the critic sees it   -> splitting the work
    agents           multi-agent brief after the critic loop       -> the critic, with agents
Drafts come free from every run with a critic (review/round-0/brief.md). A multi-agent
draft is `agents_draft`; a reviewed single prompt's draft is the same call as `informed`,
so it counts as one more `informed` brief.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CONDITIONS = ("naive", "informed", "informed_critic", "agents_draft", "agents")
CONDITION_LABELS = {
    "naive": "Single prompt (naive)",
    "informed": "Single prompt + EDA rules",
    "informed_critic": "Single prompt + EDA + critic",
    "agents_draft": "Agents, before critic",
    "agents": "Agents, after critic",
}


@dataclass(frozen=True)
class BriefRecord:
    brief_id: str
    condition: str
    run_id: str
    model: str
    recommendation: str
    markdown: str
    cost_usd: float
    wall_clock_s: float
    calls: int


@dataclass(frozen=True)
class Skipped:
    run_id: str
    reason: str
    failed: bool = False  # a comparable run that crashed: counts against reliability
    system: str | None = None  # naive | informed | informed_critic | agents
    cost_usd: float = 0.0  # spent before it failed


def _system(config: dict) -> str | None:
    """Which system made a run, from its config: baselines record their variant."""
    if config.get("variant"):
        return config["variant"] + ("_critic" if config.get("critic") else "")
    return "agents" if "max_revisions" in config else None


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect(runs_dir: Path, *, model: str, fingerprint: str | None
            ) -> tuple[list[BriefRecord], list[Skipped]]:
    """Briefs from finished runs on `model`, made with code matching `fingerprint`.

    `fingerprint=None` accepts any code version (for exploring old runs).
    """
    records: list[BriefRecord] = []
    skipped: list[Skipped] = []
    for run_dir in sorted(p for p in runs_dir.iterdir() if p.is_dir()) if runs_dir.exists() \
            else []:
        run_id = run_dir.name
        config = _load(run_dir / "config.json") if (run_dir / "config.json").exists() else {}
        if config.get("model") != model:
            skipped.append(Skipped(run_id, f"model {config.get('model')}"))
            continue
        if fingerprint and config.get("code_fingerprint") != fingerprint:
            skipped.append(Skipped(run_id, "made with different code or prompts"))
            continue
        if (run_dir / "error.json").exists() or not (run_dir / "run.json").exists():
            error = _load(run_dir / "error.json") if (run_dir / "error.json").exists() else {}
            spent = _load(run_dir / "usage.json")["totals"]["cost_usd"] \
                if (run_dir / "usage.json").exists() else 0.0
            skipped.append(Skipped(
                run_id, f"failed: {error.get('type', 'unknown')}: {error.get('message', '')}",
                failed=True, system=_system(config), cost_usd=spent))
            continue
        run = _load(run_dir / "run.json")
        usage = _load(run_dir / "usage.json")
        totals = usage["totals"]
        final = (run_dir / "brief.md").read_text(encoding="utf-8")
        mode = run["mode"]
        condition = mode.removeprefix("baseline-").replace("-", "_")
        if mode.startswith("baseline-") and condition in CONDITIONS:
            if run.get("rounds"):  # reviewed: its first draft is a plain single prompt
                records.append(_draft_record(run_dir, run, usage, model,
                                             condition.removesuffix("_critic")))
            records.append(BriefRecord(
                brief_id=run_id, condition=condition, run_id=run_id,
                model=model, recommendation=run["recommendation"], markdown=final,
                cost_usd=totals["cost_usd"], wall_clock_s=totals["wall_clock_s"],
                calls=totals["calls"]))
        elif mode == "agents":
            records.append(_draft_record(run_dir, run, usage, model, "agents_draft"))
            records.append(BriefRecord(
                brief_id=run_id, condition="agents", run_id=run_id, model=model,
                recommendation=run["recommendation"], markdown=final,
                cost_usd=totals["cost_usd"], wall_clock_s=totals["wall_clock_s"],
                calls=totals["calls"]))
        else:
            skipped.append(Skipped(run_id, f"unknown mode {mode}"))
    return records, skipped


def _draft_record(run_dir: Path, run: dict, usage: dict, model: str, condition: str
                  ) -> BriefRecord:
    """The first draft, costed as if the run had stopped before the critic.

    Critic reviews and writer revisions all happen after the draft, one after another, so
    removing their latency from the wall clock gives the time to the draft.
    """
    after_draft = [c for c in usage["calls"]
                   if c["agent"] == "critic" or c["step"].startswith("revision")]
    cost_after = sum(c["cost_usd"] or 0 for c in after_draft)
    time_after = sum(c["latency_s"] for c in after_draft)
    totals = usage["totals"]
    return BriefRecord(
        brief_id=f"{run['run_id']}#draft", condition=condition, run_id=run["run_id"],
        model=model, recommendation=run["rounds"][0]["recommendation"],
        markdown=(run_dir / "review" / "round-0" / "brief.md").read_text(encoding="utf-8"),
        cost_usd=round(totals["cost_usd"] - cost_after, 6),
        wall_clock_s=round(totals["wall_clock_s"] - time_after, 3),
        calls=totals["calls"] - len(after_draft),
    )
