"""Demo app: replay a recorded run, agent by agent. No API calls.

    uv run discovery-chef demo

Shows what each agent produced, what the critic objected to round by round, how the
brief changed, every citation traced back to its source, and the evaluation results.

Every term the app shows links to its entry on the Help page (glossary.py), and has the
same one-line definition as a hover tooltip.
"""

from __future__ import annotations

import difflib
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from discovery_chef.citations import check_brief, citation_ids
from discovery_chef.context import load_context
from discovery_chef.glossary import GROUPS, TERMS, TERMS_BY_SLUG, Term
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
TABS = ["Overview", "Agents", "Critic", "Final brief", "Comparison"]
PAGES: dict[str, st.Page] = {}


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
    PAGES["replay"] = st.Page(replay_page, title="Run replay", icon=":material/play_circle:",
                              default=True)
    PAGES["help"] = st.Page(help_page, title="Help: terms", icon=":material/help:",
                            url_path="help")
    st.navigation(list(PAGES.values())).run()


# --- links to the Help page --------------------------------------------------------------------

def tip(slug: str) -> str:
    """The term's one-line definition, for hover tooltips."""
    return TERMS_BY_SLUG[slug].short


def term_link(slug: str, label: str | None = None) -> None:
    st.page_link(PAGES["help"], label=label or TERMS_BY_SLUG[slug].name,
                 icon=":material/help_outline:", query_params={"term": slug}, help=tip(slug))


def terms_row(*slugs: str, label: str = "Terms:") -> None:
    """A row of links to the Help page for the terms used just above or below."""
    with st.container(horizontal=True, gap="small", vertical_alignment="center"):
        st.caption(label, width="content")
        for slug in slugs:
            term_link(slug)


def columns_help(**slugs: str) -> dict:
    """Column tooltips for st.dataframe: column name -> glossary slug."""
    return {column: st.column_config.Column(help=tip(slug)) for column, slug in slugs.items()}


# --- the run replay ----------------------------------------------------------------------------

def replay_page() -> None:
    st.title("PantryPal discovery: agents at work")
    st.caption("A recorded run replayed step by step. Nothing here calls a model. Click any "
               "term marked with (?) to see what it means.")

    runs = finished_runs()
    if not runs:
        st.error("No finished runs in outputs/runs/. Run `uv run discovery-chef run` first.")
        return
    agent_runs = [r for r in runs if r["mode"] == "agents"]
    choices = agent_runs + [r for r in runs if r["mode"] != "agents"]
    ids = [r["run_id"] for r in choices]
    remembered = st.session_state.get("run_id")  # survives a visit to the Help page
    choice = st.sidebar.selectbox(
        "Recorded run", choices, index=ids.index(remembered) if remembered in ids else 0,
        format_func=lambda r: f"{r['run_id']} · {r['mode']} · {r['model']}", help=tip("run"))
    st.session_state["run_id"] = choice["run_id"]
    run_dir = Path(choice["dir"])
    run = _load(run_dir / "run.json")
    usage = _load(run_dir / "usage.json")
    with st.sidebar:
        terms_row("run", "run_mode", "model")
        st.markdown("**Pipeline**\n\nresearch ∥ market → risk → writer → critic ⟲")
        terms_row("pipeline", "critic_loop")
        st.caption("Pick a `baseline-*` run to see the single-prompt version.")
        terms_row("single_prompt", "naive", "informed", "informed_critic")

    totals = usage["totals"]
    cols = st.columns(5)
    cols[0].metric("Recommendation", run["recommendation"].replace("_", " "),
                   help=tip("recommendation"))
    cols[1].metric("Critic loop", run.get("loop_outcome", "n/a"), help=tip("critic_loop"))
    cols[2].metric("Cost (list price)", f"${totals['cost_usd']:.3f}", help=tip("cost"))
    cols[3].metric("Wall clock", f"{totals['wall_clock_s'] / 60:.1f} min",
                   help=tip("wall_clock"))
    cols[4].metric("Model calls", totals["calls"], help=tip("model_calls"))
    terms_row("recommendation", "critic_loop", "cost", "wall_clock", "model_calls")

    remembered_tab = st.session_state.get("active_tab")
    tabs = st.tabs(TABS, key="replay_tab", on_change=_remember_tab,
                   default=remembered_tab if remembered_tab in TABS else None)
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


def _remember_tab() -> None:
    st.session_state["active_tab"] = st.session_state["replay_tab"]


def _overview(usage: dict) -> None:
    st.subheader("Who did what, at what cost")
    per_agent = pd.DataFrame([
        {"agent": AGENT_LABELS.get(name, name), "calls": a["calls"],
         "tool calls": a["tool_calls"], "input tokens": a["input_tokens"],
         "output tokens": a["output_tokens"], "cost ($)": round(a["cost_usd"], 4),
         "model time (s)": round(a["latency_s"], 1)}
        for name, a in usage["per_agent"].items()])
    st.dataframe(per_agent, hide_index=True, width="stretch", column_config=columns_help(**{
        "agent": "agent", "calls": "model_calls", "tool calls": "tool_calls",
        "input tokens": "input_tokens", "output tokens": "output_tokens", "cost ($)": "cost",
        "model time (s)": "model_time"}))
    terms_row("agent", "model_calls", "tool_calls", "input_tokens", "output_tokens", "cost",
              "model_time")
    tools = usage["tool_calls"]
    if tools:
        st.subheader("Tool calls: what the agents chose to look at")
        st.dataframe(pd.DataFrame([
            {"agent": AGENT_LABELS.get(t["agent"], t["agent"]), "tool": t["tool"],
             "input": json.dumps(t["input"], ensure_ascii=False)[:120],
             "sources returned": ", ".join(t["result_ids"][:12])
             + (" ..." if len(t["result_ids"]) > 12 else "")}
            for t in tools]), hide_index=True, width="stretch", column_config=columns_help(
                **{"tool": "tool_calls", "sources returned": "citation_id"}))
        terms_row("tool_calls", "citation_id")


def _agents(run_dir: Path) -> None:
    agents_dir = run_dir / "agents"
    if not agents_dir.exists():
        st.info("Single-prompt run: one call wrote the whole brief, so there are no "
                "intermediate hand-offs.")
        terms_row("single_prompt", "handoff")
        return
    research = _load(agents_dir / "research_synthesis.json")
    market = _load(agents_dir / "market_analysis.json")
    risk = _load(agents_dir / "risk_analysis.json")
    st.caption("Each section is one agent's hand-off: the structured output it passed on.")
    terms_row("agent", "handoff", "pipeline")

    st.subheader("1. Research synthesiser: interviews in, users and problems out")
    terms_row("research_synthesiser", "segment", "target_fit", "insight", "strength",
              "own_words", "evidence_kind", "caveat")
    st.dataframe(pd.DataFrame([{"segment": s["name"], "fit": s["target_fit"],
                                "interviews": ", ".join(s["interview_ids"])}
                               for s in research["segments"]]), hide_index=True,
                 column_config=columns_help(segment="segment", fit="target_fit",
                                            interviews="citation_id"))
    for insight in research["insights"]:
        with st.expander(f"{insight['id']} · {insight['kind']} · {insight['strength']}: "
                         f"{insight['statement']}"):
            st.write(f"Interviews: {', '.join(insight['interview_ids'])} (own words: "
                     f"{', '.join(insight['own_words_interviews']) or 'none'})")
            for e in insight["evidence"]:
                st.markdown(f"- `{e['source_id']}` ({e['kind']}): \"{e['quote']}\"")
            for caveat in insight["caveats"]:
                st.caption(f"Caveat: {caveat}")
            terms_row("insight", "strength", "own_words", "evidence_kind", "caveat")

    st.subheader("2. Market analyst: competitors and statistics in, landscape out")
    terms_row("market_analyst", "threat", "data_quality", "overlap", "claim_check")
    st.dataframe(pd.DataFrame([{"competitor": c["competitor"], "threat": c["threat"],
                                "data": c["data_quality"],
                                "overlap": ", ".join(c["overlap_with_pantrypal"])}
                               for c in market["competitors"]]), hide_index=True,
                 column_config=columns_help(threat="threat", data="data_quality",
                                            overlap="overlap"))
    st.markdown("**Claim checks on the idea brief**")
    for check in market["idea_claim_checks"]:
        st.markdown(f"- **{check['verdict']}**: {check['claim']} "
                    f"({', '.join(check['source_ids'])})")

    st.subheader("3. Risk analyst: both analyses in, ranked assumptions out")
    terms_row("risk_analyst", "assumption", "riskiest", "experiment", "success_metric")
    by_id = {a["id"]: a for a in risk["assumptions"]}
    st.dataframe(pd.DataFrame([
        {"rank": i + 1, "assumption": by_id[a]["statement"], "type": by_id[a]["category"],
         "confidence": by_id[a]["confidence"], "impact if wrong": by_id[a]["impact_if_wrong"]}
        for i, a in enumerate(risk["riskiest_assumptions"]) if a in by_id]), hide_index=True,
        column_config=columns_help(**{"rank": "riskiest", "assumption": "assumption",
                                      "type": "assumption", "confidence": "assumption",
                                      "impact if wrong": "assumption"}))
    for experiment in risk["experiments"]:
        st.markdown(f"- **{experiment['id']}** {experiment['hypothesis']}  \n"
                    f"  Method: {experiment['method']}  \n"
                    f"  Success metric: {experiment['success_metric']}")


def _critic(run_dir: Path, run: dict) -> None:
    rounds = run.get("rounds")
    if not rounds:
        st.info("Single-prompt run: no critic loop.")
        terms_row("critic_loop", "informed_critic")
        return
    st.subheader(f"The critic loop: {run['loop_outcome']} after {len(rounds)} round(s)")
    terms_row("critic", "critic_loop", "verdict", "objection", "severity", "citation_check",
              "blocking_issue", "claim_coverage")
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
        terms_row("revision_diff")
        diff = difflib.unified_diff(first.splitlines(), final.splitlines(), "first draft",
                                    "final brief", lineterm="", n=0)
        st.code("\n".join(diff), language="diff")


def _brief(run_dir: Path) -> None:
    brief = (run_dir / "brief.md").read_text(encoding="utf-8")
    ctx = context()
    report = check_brief(brief, ctx)
    left, right = st.columns([3, 2])
    with left:
        terms_row("brief_sections", "recommendation", "citation_id", "unsupported_tag")
        st.markdown(brief)
    with right:
        st.subheader("Trace a citation")
        terms_row("trace_citation", "citation_id")
        ids = sorted({i for line in brief.splitlines() for i in citation_ids(line)
                      if i != "UNSUPPORTED"})
        chosen = st.selectbox(f"{len(ids)} cited sources", ids, help=tip("trace_citation"))
        text = ctx.source_text(chosen) if chosen else None
        st.code(text or "Unknown source ID", language="xml")
        st.subheader("Automated citation check")
        terms_row("citation_check", "blocking_issue", "claim_coverage", "verified_quote")
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
    st.caption("Averages over every scored brief of each system. These results don't depend "
               "on the run selected in the sidebar.")
    st.dataframe(shown, hide_index=True, width="stretch", column_config=columns_help(**{
        "system": "condition", "n": "n_briefs", "quality (0-1)": "quality_index",
        "traps handled": "trap", "misrepresented sources": "misrepresentation",
        "criteria (1-5)": "criteria", "cost ($)": "cost", "time (s)": "wall_clock",
        "calls": "model_calls"}))
    terms_row("condition", "n_briefs", "quality_index", "trap", "misrepresentation",
              "criteria", "cost", "wall_clock", "model_calls")
    figure = eval_dir / "figures" / "quality_vs_cost.png"
    if figure.exists():
        st.image(str(figure))
        terms_row("quality_vs_cost")
    report = eval_dir / "eval_report.md"
    if report.exists():
        with st.expander("Full evaluation report"):
            terms_row("judge", "fingerprint", "trap", "criteria", "condition")
            st.markdown(report.read_text(encoding="utf-8"))


# --- the Help page -----------------------------------------------------------------------------

def help_page() -> None:
    st.title("Help: terms used in this app")
    st.caption("Every term marked with (?) in the run replay links here. Each entry says what "
               "the term means, how it is worked out, and gives an example from this data.")
    term = TERMS_BY_SLUG.get(st.query_params.get("term", ""))
    if term:
        st.query_params["term"] = term.slug  # keep the address bar in step on same-page links
        with st.container(border=True):
            st.caption(term.group)
            st.header(term.name, anchor=term.slug)
            _term_body(term)
        st.page_link(PAGES["replay"], label="Back to the run replay",
                     icon=":material/arrow_back:")
        st.divider()

    query = st.text_input("Search all terms", placeholder="for example: tokens, critic, tier")
    found = [t for t in TERMS if _matches(t, query)]
    if query and not found:
        st.info("No term matches that search.")
    for group in GROUPS:
        members = [t for t in found if t.group == group]
        if not members:
            continue
        st.subheader(group, anchor=False)
        for t in members:
            with st.expander(t.name, expanded=bool(query) or t is term):
                _term_body(t)


def _term_body(term: Term) -> None:
    st.markdown(f"**{term.short}**")
    st.markdown(term.detail)
    st.info(term.example, title="Example", icon=":material/lightbulb:")
    if term.related:
        terms_row(*term.related, label="Related:")


def _matches(term: Term, query: str) -> bool:
    words = query.lower().split()
    text = " ".join((term.name, term.short, term.detail, term.example)).lower()
    return all(word in text for word in words)


if __name__ == "__main__":
    main()
