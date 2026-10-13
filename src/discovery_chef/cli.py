"""Command-line entry point: `uv run discovery-chef <stage>`.

Stages run in order; each writes to `outputs/` and later stages read from there.
    eda       Phase 1 - profile the data and write outputs/eda/evidence_profile.json
    search    Try the interview retrieval the agents use (no API calls)
    run         Phase 2 - multi-agent discovery brief   -> outputs/runs/<id>-agents/
    baseline    Phase 2 - single-prompt discovery brief -> outputs/runs/<id>-baseline-<variant>/
    experiment  Phase 3 - every system N times          -> outputs/runs/
    evaluate    Phase 3 - score and compare the runs    -> outputs/eval/
    demo        Replay recorded runs in the browser (no API calls)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from discovery_chef.paths import EDA_OUTPUT_DIR, NOTEBOOKS_DIR, REPO_ROOT

EDA_NOTEBOOK = NOTEBOOKS_DIR / "01_eda.ipynb"
ENV_FILE = REPO_ROOT / ".env"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="discovery-chef", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    stages = parser.add_subparsers(dest="stage", required=True)

    eda = stages.add_parser("eda", help="Phase 1: exploratory data analysis -> outputs/eda/")
    eda.add_argument("--no-figures", action="store_true", help="skip the PNG figures")
    eda.add_argument("--notebook", action="store_true",
                     help=f"also re-execute {EDA_NOTEBOOK.relative_to(REPO_ROOT)} in place")

    search = stages.add_parser("search", help="search the interviews like the agents do")
    search.add_argument("query")
    search.add_argument("-k", type=int, default=5)

    run = stages.add_parser("run", help="Phase 2: multi-agent discovery brief")
    _add_model_options(run)
    run.add_argument("--max-revisions", type=int, default=2,
                     help="critic/writer revision rounds after the first draft (default 2)")

    baseline = stages.add_parser("baseline", help="Phase 2: single-prompt discovery brief")
    _add_model_options(baseline)
    baseline.add_argument("--variant", choices=("naive", "informed"), default="naive",
                          help="naive = raw data only; informed = plus the EDA rules")

    experiment = stages.add_parser(
        "experiment", help="Phase 3: run naive, informed and multi-agent N times each")
    _add_model_options(experiment)
    experiment.add_argument("--repeats", type=int, default=3)
    experiment.add_argument("--max-revisions", type=int, default=2)

    evaluate = stages.add_parser("evaluate", help="Phase 3: score and compare runs")
    evaluate.add_argument("--model", default=None,
                          help="compare runs made with this model (default: the run default)")
    evaluate.add_argument("--judge-model", default=None,
                          help="model for the LLM judge (default gemini-3.1-pro-preview)")
    evaluate.add_argument("--no-judge", action="store_true",
                          help="automatic checks only, plus cached judge verdicts (free)")
    evaluate.add_argument("--fingerprint", default=None,
                          help="compare runs made with this code version (default: current)")
    evaluate.add_argument("--all-versions", action="store_true",
                          help="include runs made with any code or prompts")

    stages.add_parser("demo", help="replay recorded runs in the browser (no API calls)")

    args = parser.parse_args(argv)
    if args.stage == "eda":
        return _run_eda(args)
    if args.stage == "demo":
        return _demo()
    if args.stage == "search":
        return _search(args)
    _load_env_file()
    stage = {"run": _run_agents, "baseline": _run_baseline, "experiment": _run_experiment,
             "evaluate": _evaluate}[args.stage]
    try:
        if args.stage == "evaluate":
            if not args.no_judge:
                _check_credentials()  # the judge runs on Gemini
        else:
            _resolve_model_options(args)
            _check_provider(args)
        return stage(args)
    except _UserFacingError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _add_model_options(parser: argparse.ArgumentParser) -> None:
    from discovery_chef.llm import DEFAULT_MODELS, EFFORTS, PROVIDERS, LLMConfig

    parser.add_argument("--provider", default="gemini", choices=PROVIDERS,
                        help="gemini = Google's API (needs a key); ollama = local models "
                        "(free, slower)")
    parser.add_argument("--model", default=None,
                        help="default: " + ", ".join(f"{m} for {p}"
                                                     for p, m in DEFAULT_MODELS.items()))
    parser.add_argument("--effort", default=None, choices=EFFORTS,
                        help="thinking level (default: medium for gemini; low = no thinking "
                        "for ollama)")
    parser.add_argument("--max-tokens", type=int, default=LLMConfig.max_tokens,
                        help="output ceiling per call, thinking included")
    parser.add_argument("--num-ctx", type=int, default=LLMConfig.num_ctx,
                        help="ollama only: context window in tokens (more needs more memory)")


def _resolve_model_options(args) -> None:
    from discovery_chef.llm import DEFAULT_EFFORT, DEFAULT_MODELS

    args.model = args.model or DEFAULT_MODELS[args.provider]
    args.effort = args.effort or DEFAULT_EFFORT[args.provider]


def _check_provider(args) -> None:
    """Fail before creating a run folder if the chosen provider cannot work."""
    if args.provider == "gemini":
        _check_credentials()
        return
    from discovery_chef.llm import LLMError
    from discovery_chef.llm.ollama import installed_models

    try:
        installed = installed_models()
    except LLMError as error:
        raise _UserFacingError(str(error)) from error
    names = set(installed) | {name.removesuffix(":latest") for name in installed}
    if args.model not in names:
        raise _UserFacingError(f"Ollama model {args.model!r} is not installed. Run `ollama "
                               f"pull {args.model}` (installed: {', '.join(installed)})")


class _UserFacingError(Exception):
    pass


CREDENTIAL_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY")
NO_CREDENTIALS = ("no Gemini API key found. Put GEMINI_API_KEY=... in .env (see .env.example) "
                  "or export it. Keys: https://aistudio.google.com/apikey")


def _check_credentials() -> None:
    """Fail before creating a run folder when no API key is set."""
    if not any(os.environ.get(name) for name in CREDENTIAL_VARS):
        raise _UserFacingError(NO_CREDENTIALS)


# --- Phase 1 ------------------------------------------------------------------------------

def _run_eda(args) -> int:
    from discovery_chef.eda import run_eda

    # Always outputs/eda/: Phase 2 and the notebook read from there.
    profile = run_eda(EDA_OUTPUT_DIR, figures=not args.no_figures)
    tiers = profile.metrics.set_index("interview_id")["evidence_tier"]
    print(f"EDA written to {_display(EDA_OUTPUT_DIR)}")
    print(f"  research date      {profile.dataset.as_of}")
    for tier in ("primary", "supporting", "contrast_only", "excluded"):
        ids = ", ".join(tiers.index[tiers == tier]) or "-"
        print(f"  {tier:<18} {ids}")
    print(f"  findings           {len(profile.findings)} "
          f"({sum(f.headline for f in profile.findings)} headline)")
    if args.notebook:
        execute_notebook(EDA_NOTEBOOK)
        print(f"Notebook executed: {_display(EDA_NOTEBOOK)}")
    return 0


def execute_notebook(path: Path, timeout: int = 600) -> None:
    import nbformat
    from nbclient import NotebookClient

    notebook = nbformat.read(path, as_version=4)
    for cell in notebook.cells:  # keep re-runs diff-free
        cell.metadata.pop("execution", None)
    NotebookClient(notebook, timeout=timeout, kernel_name="python3", record_timing=False,
                   resources={"metadata": {"path": str(path.parent)}}).execute()
    nbformat.write(notebook, path)


# --- Phase 2 ------------------------------------------------------------------------------

def _context():
    from discovery_chef.context import StaleProfileError, load_context

    try:
        return load_context()
    except StaleProfileError as error:
        raise _UserFacingError(str(error)) from error


def _search(args) -> int:
    ctx = _context()
    for hit in ctx.index.search(args.query, k=args.k):
        print(f"[{hit.score:6.2f}] {hit.passage.render()}\n")
    return 0


def _llm(args):
    from discovery_chef.llm import LLMConfig, RunTracker, create_llm

    config = LLMConfig(provider=args.provider, model=args.model, effort=args.effort,
                       max_tokens=args.max_tokens, num_ctx=args.num_ctx)
    tracker = RunTracker()
    return create_llm(config, tracker), config, tracker


def _run_agents(args) -> int:
    from discovery_chef.orchestrator import review_markdown, run_pipeline
    from discovery_chef.runs import RunRecorder, code_fingerprint

    ctx = _context()
    llm, config, tracker = _llm(args)
    recorder = RunRecorder("agents")
    run_config = {**vars(config), "max_revisions": args.max_revisions,
                  "code_fingerprint": code_fingerprint()}
    recorder.json("config.json", run_config)
    print(f"Run {recorder.run_id}: research + market (parallel) -> risk -> writer -> critic "
          f"({config.provider} {config.model}, effort {config.effort})")
    with _api_errors(recorder, tracker):
        result = run_pipeline(llm, ctx, recorder, max_revisions=args.max_revisions)

    recorder.text("brief.md", result.brief.markdown)
    recorder.json("brief.json", result.brief)
    recorder.json("citation_check.json", result.final_check.to_dict())
    recorder.text("review.md", review_markdown(result))
    summary = tracker.summary()
    recorder.json("run.json", {
        "run_id": recorder.run_id, "mode": "agents", "started_at": recorder.started_at.isoformat(),
        "config": run_config,
        "recommendation": result.brief.recommendation,
        "loop_outcome": result.loop_outcome,
        "rounds": [vars(r) | {"serious": r.serious} for r in result.rounds],
        "final_citation_check": result.final_check.to_dict(),
        "totals": summary["totals"],
    })
    _print_result(recorder, summary, result.brief.recommendation, result.final_check,
                  extra=f"critic loop: {result.loop_outcome} after {len(result.rounds)} round(s)")
    return 0


def _run_baseline(args) -> int:
    from discovery_chef.baseline import run_baseline
    from discovery_chef.citations import check_brief
    from discovery_chef.runs import RunRecorder, code_fingerprint

    ctx = _context()
    llm, config, tracker = _llm(args)
    recorder = RunRecorder(f"baseline-{args.variant}")
    run_config = {**vars(config), "variant": args.variant,
                  "code_fingerprint": code_fingerprint()}
    recorder.json("config.json", run_config)
    print(f"Run {recorder.run_id}: single prompt ({args.variant}, {config.provider} "
          f"{config.model}, effort {config.effort})")
    with _api_errors(recorder, tracker):
        brief = run_baseline(llm, ctx, args.variant)

    check = check_brief(brief.markdown, ctx)
    recorder.text("brief.md", brief.markdown)
    recorder.json("brief.json", brief)
    recorder.json("citation_check.json", check.to_dict())
    summary = tracker.summary()
    recorder.json("run.json", {
        "run_id": recorder.run_id, "mode": f"baseline-{args.variant}",
        "started_at": recorder.started_at.isoformat(),
        "config": run_config,
        "recommendation": brief.recommendation, "final_citation_check": check.to_dict(),
        "totals": summary["totals"],
    })
    _print_result(recorder, summary, brief.recommendation, check)
    return 0


# --- Phase 3 ------------------------------------------------------------------------------

def _run_experiment(args) -> int:
    """Every system `--repeats` times, interleaved so time-of-day effects (load, outages)
    spread evenly across systems. A failed run is reported and skipped, not fatal."""
    plan = [("baseline", "naive"), ("baseline", "informed"), ("run", None)]
    failures = []
    for repeat in range(1, args.repeats + 1):
        for stage, variant in plan:
            name = f"{stage}{f' {variant}' if variant else ''}"
            print(f"\n=== repeat {repeat}/{args.repeats}: {name}")
            run_args = argparse.Namespace(**vars(args), variant=variant)
            try:
                (_run_agents if stage == "run" else _run_baseline)(run_args)
            except _UserFacingError as error:
                failures.append(f"repeat {repeat} {name}: {error}")
                print(f"error: {error}", file=sys.stderr)
    print(f"\nExperiment finished: {args.repeats * len(plan) - len(failures)} runs succeeded, "
          f"{len(failures)} failed.")
    for failure in failures:
        print(f"  {failure}")
    print("Next: uv run discovery-chef evaluate")
    return 1 if failures else 0


def _evaluate(args) -> int:
    from discovery_chef.eval.collect import collect
    from discovery_chef.eval.judge import JUDGE_MODEL
    from discovery_chef.eval.report import evaluate
    from discovery_chef.llm import DEFAULT_MODEL, LLMConfig, RunTracker, create_llm
    from discovery_chef.paths import OUTPUTS_DIR
    from discovery_chef.runs import RUNS_DIR, code_fingerprint

    ctx = _context()
    model = args.model or DEFAULT_MODEL
    fingerprint = None if args.all_versions else (args.fingerprint or code_fingerprint())
    records, skipped = collect(RUNS_DIR, model=model, fingerprint=fingerprint)
    if not records:
        versions = _fingerprints_on_disk(RUNS_DIR, model)
        raise _UserFacingError(
            f"no finished runs on {model} with code fingerprint {fingerprint}. Run "
            "`uv run discovery-chef experiment` first, or pass --fingerprint with one of: "
            + (", ".join(f"{fp} ({n} runs)" for fp, n in versions.items()) or "none found"))

    judge_model = args.judge_model or JUDGE_MODEL
    tracker = RunTracker()
    judge_llm = None if args.no_judge else create_llm(
        LLMConfig(provider="gemini", model=judge_model, effort="high"), tracker)
    out_dir = OUTPUTS_DIR / "eval"
    setup = {"model under test": model,
             "code fingerprint": fingerprint or "any",
             "judge model": "cached verdicts only" if args.no_judge else judge_model}
    try:
        result = evaluate(records, ctx, RUNS_DIR, out_dir, judge_llm=judge_llm,
                          judge_model=judge_model, cache_dir=out_dir / "judge",
                          skipped=skipped, setup=setup)
    except Exception as error:
        from google.genai import errors

        from discovery_chef.llm import LLMError

        if isinstance(error, (LLMError, errors.APIError)):
            raise _UserFacingError(f"judge failed: {error}") from error
        raise

    summary = result.summary
    print(f"Evaluated {len(records)} briefs ({len(skipped)} runs left out) -> "
          f"{_display(out_dir)}/eval_report.md")
    for _, row in summary.iterrows():
        quality = "-" if pd_isna(row["quality_index"]) else f"{row['quality_index']:.2f}"
        print(f"  {row['label']:<28} n={int(row['n'])}  quality {quality}  "
              f"cost ${row['cost_usd']:.3f}  time {row['wall_clock_s']:.0f}s")
    if judge_llm and tracker.calls:
        print(f"  judge cost ${tracker.summary()['totals']['cost_usd']:.3f} over "
              f"{len(tracker.calls)} calls")
    return 0


def _demo() -> int:
    import subprocess

    app = Path(__file__).parent / "demo.py"
    return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)])


def _fingerprints_on_disk(runs_dir: Path, model: str) -> dict[str, int]:
    import json
    from collections import Counter

    counts: Counter[str] = Counter()
    for config_path in runs_dir.glob("*/config.json"):
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config.get("model") == model and config.get("code_fingerprint"):
            counts[config["code_fingerprint"]] += 1
    return dict(counts.most_common())


def pd_isna(value) -> bool:
    return value is None or value != value  # NaN is the only value not equal to itself


class _api_errors:
    """Always save usage, and turn auth/API failures into a readable message."""

    def __init__(self, recorder, tracker):
        self.recorder, self.tracker = recorder, tracker

    def __enter__(self):
        return self

    def __exit__(self, exc_type, error, tb):
        from google.genai import errors

        from discovery_chef.llm import LLMError

        self.tracker.finish()
        self.recorder.json("usage.json", self.tracker.summary())
        if error is None:
            return False
        self.recorder.json("error.json", {"type": exc_type.__name__, "message": str(error)})
        saved = f"(partial run saved in {_display(self.recorder.dir)})"
        if isinstance(error, errors.ClientError) and error.code in (401, 403):
            raise _UserFacingError(f"the Gemini API rejected the key: {error.message} "
                                   f"{saved}") from error
        if isinstance(error, errors.ClientError) and error.code == 429:
            raise _UserFacingError(f"rate limit or quota exhausted after retries: "
                                   f"{error.message} {saved}") from error
        if isinstance(error, (LLMError, errors.APIError)):
            raise _UserFacingError(f"{type(error).__name__}: {error} {saved}") from error
        return False


def _print_result(recorder, summary, recommendation, check, extra: str = "") -> None:
    totals = summary["totals"]
    cost = f"${totals['cost_usd']:.4f}" + (" (incomplete)" if totals["cost_incomplete"] else "")
    print(f"Done: {_display(recorder.dir)}")
    print(f"  recommendation     {recommendation}")
    if extra:
        print(f"  {extra}")
    print(f"  citation check     {'passed' if check.passed else 'FAILED'} "
          f"({check.citations} citations, coverage {check.coverage:.0%}, "
          f"{check.blocking} blocking)")
    print(f"  cost               {cost} over {totals['calls']} calls")
    print(f"  latency            {totals['wall_clock_s']:.1f}s wall clock "
          f"({totals['model_time_s']:.1f}s model time)")
    for agent, agg in summary["per_agent"].items():
        print(f"    {agent:<22} ${agg['cost_usd']:.4f}  {agg['latency_s']:6.1f}s  "
              f"{agg['calls']} calls  {agg['tool_calls']} tool calls")


def _load_env_file(path: Path | None = None) -> None:
    """Load KEY=VALUE lines from .env without overriding the real environment."""
    path = path or ENV_FILE  # looked up at call time, so tests can redirect it
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _display(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
