"""Demo app: replay a recorded run, agent by agent. No API calls.

    uv run discovery-chef demo

Shows what each agent produced, what the critic objected to round by round, how the
brief changed, every citation traced back to its source, and the evaluation results.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from discovery_chef.citations import check_brief, citation_ids
from discovery_chef.context import load_context
from discovery_chef.paths import OUTPUTS_DIR
from discovery_chef.runs import RUNS_DIR

AGENT_LABELS = {
    "research_synthesiser": "Research synthesiser",
    "market_analyst": "Market analyst",
    "risk_analyst": "Risk analyst",
    "brief_writer": "Brief writer",
    "critic": "Critic",
}
SEVERITY_ICON = {"blocker": "⛔", "major": "⚠️", "minor": "ℹ️"}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@st.cache_resource
def context():
    return load_context()


@st.cache_data
def finished_runs() -> list[dict]:
    runs = []
    for run_dir in sorted(RUNS_DIR.glob("*"), reverse=True):
        if (run_dir / "run.json").exists() and not (run_dir / "error.json").exists():
            run = _load(run_dir / "run.json")
            runs.append({"dir": str(run_dir), "run_id": run["run_id"], "mode": run["mode"],
                         "model": run["config"]["model"],
                         "provider": run["config"].get("provider", "gemini")})
    return runs


def main() -> None:
    st.set_page_config(page_title="PantryPal discovery agents", layout="wide")
    st.title("PantryPal discovery: agents at work")
    st.caption("A recorded run replayed step by step. Nothing here calls a model.")

    runs = finished_runs()
    if not runs:
        st.error("No finished runs in outputs/runs/. Run `uv run discovery-chef run` first.")
        return
    agent_runs = [r for r in runs if r["mode"] == "agents"]
    choices = agent_runs + [r for r in runs if r["mode"] != "agents"]
    choice = st.sidebar.selectbox(
        "Recorded run", choices,
        format_func=lambda r: f"{r['run_id']} · {r['mode']} · {r['model']}")
    run_dir = Path(choice["dir"])
    run = _load(run_dir / "run.json")
    usage = _load(run_dir / "usage.json")
    st.sidebar.markdown("**Pipeline**\n\nresearch ∥ market → risk → writer → critic ⟲")
    st.sidebar.caption("Pick a `baseline-*` run to see the single-prompt version.")

    totals = usage["totals"]
    cols = st.columns(5)
    cols[0].metric("Recommendation", run["recommendation"].replace("_", " "))
    cols[1].metric("Critic loop", run.get("loop_outcome", "n/a"))
    cols[2].metric("Cost (list price)", f"${totals['cost_usd']:.3f}")
    cols[3].metric("Wall clock", f"{totals['wall_clock_s'] / 60:.1f} min")
    cols[4].metric("Model calls", totals["calls"])

    tabs = st.tabs(["Overview", "Agents", "Critic", "Final brief", "Comparison"])
    with tabs[0]:
        _overview(usage)
    with tabs[1]:
        _agents(run_dir)
    with tabs[2]:
        _critic(run_dir, run)
    with tabs[3]:
        _brief(run_dir)
    with tabs[4]:
        _comparison()


def _overview(usage: dict) -> None:
    st.subheader("Who did what, at what cost")
    per_agent = pd.DataFrame([
        {"agent": AGENT_LABELS.get(name, name), "calls": a["calls"],
         "tool calls": a["tool_calls"], "input tokens": a["input_tokens"],
         "output tokens": a["output_tokens"], "cost ($)": round(a["cost_usd"], 4),
         "model time (s)": round(a["latency_s"], 1)}
        for name, a in usage["per_agent"].items()])
    st.dataframe(per_agent, hide_index=True, width="stretch")
    tools = usage["tool_calls"]
    if tools:
        st.subheader("Tool calls: what the agents chose to look at")
        st.dataframe(pd.DataFrame([
            {"agent": AGENT_LABELS.get(t["agent"], t["agent"]), "tool": t["tool"],
             "input": json.dumps(t["input"], ensure_ascii=False)[:120],
             "sources returned": ", ".join(t["result_ids"][:12])
             + (" ..." if len(t["result_ids"]) > 12 else "")}
            for t in tools]), hide_index=True, width="stretch")


def _agents(run_dir: Path) -> None:
    agents_dir = run_dir / "agents"
    if not agents_dir.exists():
        st.info("Single-prompt run: one call wrote the whole brief, so there are no "
                "intermediate hand-offs.")
        return
    research = _load(agents_dir / "research_synthesis.json")
    market = _load(agents_dir / "market_analysis.json")
    risk = _load(agents_dir / "risk_analysis.json")

    st.subheader("1. Research synthesiser: interviews in, users and problems out")
    st.dataframe(pd.DataFrame([{"segment": s["name"], "fit": s["target_fit"],
                                "interviews": ", ".join(s["interview_ids"])}
                               for s in research["segments"]]), hide_index=True)
    for insight in research["insights"]:
        with st.expander(f"{insight['id']} · {insight['kind']} · {insight['strength']}: "
                         f"{insight['statement']}"):
            st.write(f"Interviews: {', '.join(insight['interview_ids'])} (own words: "
                     f"{', '.join(insight['own_words_interviews']) or 'none'})")
            for e in insight["evidence"]:
                st.markdown(f"- `{e['source_id']}` ({e['kind']}): \"{e['quote']}\"")
            for caveat in insight["caveats"]:
                st.caption(f"Caveat: {caveat}")

    st.subheader("2. Market analyst: competitors and statistics in, landscape out")
    st.dataframe(pd.DataFrame([{"competitor": c["competitor"], "threat": c["threat"],
                                "data": c["data_quality"],
                                "overlap": ", ".join(c["overlap_with_pantrypal"])}
                               for c in market["competitors"]]), hide_index=True)
    for check in market["idea_claim_checks"]:
        st.markdown(f"- **{check['verdict']}**: {check['claim']} "
                    f"({', '.join(check['source_ids'])})")

    st.subheader("3. Risk analyst: both analyses in, ranked assumptions out")
    by_id = {a["id"]: a for a in risk["assumptions"]}
    st.dataframe(pd.DataFrame([
        {"rank": i + 1, "assumption": by_id[a]["statement"], "type": by_id[a]["category"],
         "confidence": by_id[a]["confidence"], "impact if wrong": by_id[a]["impact_if_wrong"]}
        for i, a in enumerate(risk["riskiest_assumptions"]) if a in by_id]), hide_index=True)
    for experiment in risk["experiments"]:
        st.markdown(f"- **{experiment['id']}** {experiment['hypothesis']}  \n"
                    f"  Method: {experiment['method']}  \n"
                    f"  Success metric: {experiment['success_metric']}")


def _critic(run_dir: Path, run: dict) -> None:
    rounds = run.get("rounds")
    if not rounds:
        st.info("Single-prompt run: no critic loop.")
        return
    st.subheader(f"The critic loop: {run['loop_outcome']} after {len(rounds)} round(s)")
    for info in rounds:
        number = info["round"]
        critique = _load(run_dir / "review" / f"round-{number}" / "critique.json")
        check = info["citation_check"]
        st.markdown(f"#### Round {number}: {critique['verdict']}")
        st.caption(f"Automated citation check: {'passed' if check['passed'] else 'failed'} "
                   f"({check['blocking']} blocking, {check['coverage']:.0%} claim coverage)")
        st.write(critique["summary"])
        for o in critique["objections"]:
            st.markdown(f"{SEVERITY_ICON.get(o['severity'], '')} **{o['severity']}** "
                        f"({o['category']}, section {o['section']})  \n"
                        f"> {o['excerpt']}\n\n{o['problem']}  \n*Fix:* {o['fix']}")
    first = (run_dir / "review" / "round-0" / "brief.md").read_text(encoding="utf-8")
    final = (run_dir / "brief.md").read_text(encoding="utf-8")
    if first != final:
        st.markdown("#### What the revisions changed")
        diff = difflib.unified_diff(first.splitlines(), final.splitlines(), "first draft",
                                    "final brief", lineterm="", n=0)
        st.code("\n".join(diff), language="diff")


def _brief(run_dir: Path) -> None:
    brief = (run_dir / "brief.md").read_text(encoding="utf-8")
    ctx = context()
    report = check_brief(brief, ctx)
    left, right = st.columns([3, 2])
    with left:
        st.markdown(brief)
    with right:
        st.subheader("Trace a citation")
        ids = sorted({i for line in brief.splitlines() for i in citation_ids(line)
                      if i != "UNSUPPORTED"})
        chosen = st.selectbox(f"{len(ids)} cited sources", ids)
        text = ctx.source_text(chosen) if chosen else None
        st.code(text or "Unknown source ID", language="xml")
        st.subheader("Automated citation check")
        st.text(report.render())


def _comparison() -> None:
    eval_dir = OUTPUTS_DIR / "eval"
    if not (eval_dir / "summary.csv").exists():
        st.info("No evaluation yet. Run `uv run discovery-chef evaluate`.")
        return
    summary = pd.read_csv(eval_dir / "summary.csv")
    shown = summary[["label", "n", "quality_index", "trap_rate", "misrepresentations",
                     "mean_criteria", "cost_usd", "wall_clock_s", "calls"]].rename(columns={
        "label": "system", "quality_index": "quality (0-1)", "trap_rate": "traps handled",
        "misrepresentations": "misrepresented sources", "mean_criteria": "criteria (1-5)",
        "cost_usd": "cost ($)", "wall_clock_s": "time (s)"})
    st.dataframe(shown, hide_index=True, width="stretch")
    figure = eval_dir / "figures" / "quality_vs_cost.png"
    if figure.exists():
        st.image(str(figure))
    report = eval_dir / "eval_report.md"
    if report.exists():
        with st.expander("Full evaluation report"):
            st.markdown(report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
