"""Every term the demo app shows, explained with an example from this dataset.

The demo links each term to its entry on the Help page (`?term=<slug>`). The entries
describe what the code does, so keep them in step when the code changes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Term:
    slug: str  # used in the help-page URL: /help?term=<slug>
    name: str
    group: str
    short: str  # one sentence, also used as the hover tooltip
    detail: str  # Markdown
    example: str  # Markdown
    related: tuple[str, ...] = ()


RUNS = "Runs, cost and time"
AGENTS = "The systems and agents"
RESEARCH = "Research synthesiser output"
MARKET = "Market analyst output"
RISK = "Risk analyst output"
CRITIC = "The critic loop"
CHECKS = "Citations and automatic checks"
EVAL = "Evaluation and comparison"
EDA = "Evidence and the EDA"
GROUPS = (RUNS, AGENTS, RESEARCH, MARKET, RISK, CRITIC, CHECKS, EVAL, EDA)

TERMS: tuple[Term, ...] = (
    # --- runs, cost and time -----------------------------------------------------------------
    Term(
        "run", "Recorded run", RUNS,
        "One execution of a system, saved in its own folder under outputs/runs/.",
        "Every `discovery-chef run` or `discovery-chef baseline` creates a folder named "
        "`<date>-<time>-<mode>`. It holds everything the run produced: the final brief, each "
        "agent's hand-off, every critic round, the citation check, and a log of every model "
        "call with its tokens, cost and time. The demo only reads these folders; it never "
        "calls a model. Runs that crashed are not listed.",
        "`20261013-105242-agents` is a multi-agent run started on 13 October 2026 at "
        "10:52:42. Its final brief is `outputs/runs/20261013-105242-agents/brief.md`.",
        ("run_mode", "model"),
    ),
    Term(
        "run_mode", "Mode", RUNS,
        "Which system made the run: agents, or a single prompt (naive, informed, or "
        "informed with the critic).",
        "The mode is the last part of the run's name:\n\n"
        "| Mode | System |\n|---|---|\n"
        "| `agents` | the five-agent pipeline with the critic loop |\n"
        "| `baseline-naive` | one prompt, raw data only |\n"
        "| `baseline-informed` | one prompt plus the EDA's rules |\n"
        "| `baseline-informed-critic` | the informed prompt, then the same critic loop as "
        "the agents |",
        "`20261013-103406-baseline-informed` was one model call that received the raw data "
        "and the EDA's rules, with no critic.",
        ("single_prompt", "naive", "informed", "pipeline", "condition"),
    ),
    Term(
        "model", "Model", RUNS,
        "The language model that wrote the brief, such as gemini-3.8-flash.",
        "Every agent in a run uses the same model, and the single prompt uses the same model "
        "as the agents, so a comparison measures the system design, not the model. The "
        "evaluation only compares runs made with the same model. Runs with `ollama:` models "
        "ran locally on your own machine.",
        "All the runs in the current evaluation used `gemini-3.8-flash`; the judge that "
        "scored them used the stronger `gemini-3.1-pro-preview`.",
        ("judge", "fingerprint"),
    ),
    Term(
        "pipeline", "Pipeline", RUNS,
        "The fixed order the agents work in: research and market in parallel, then risk, "
        "writer and critic.",
        "```\nresearch synthesiser ─┐\n                      ├─> risk analyst ─> brief "
        "writer ─> critic ─┐\nmarket analyst ───────┘                        ^            "
        "      │ revise\n                                               └──────────────────┘"
        "\n```\n\nPlain code runs the agents in this order; no model decides who goes next. "
        "The research synthesiser and the market analyst need different inputs and nothing "
        "from each other, so they run at the same time. In the sidebar, ∥ means "
        "\"in parallel\" and ⟲ means the critic can send the brief back for revision.",
        "In run `20261013-105242-agents` the market analyst finished its whole analysis "
        "(call 4) while the research synthesiser was still reading interviews (calls 1-3 "
        "and 5-6).",
        ("research_synthesiser", "market_analyst", "risk_analyst", "brief_writer", "critic",
         "critic_loop"),
    ),
    Term(
        "recommendation", "Recommendation", RUNS,
        "The brief's verdict on PantryPal: build, pivot or test further.",
        "Every brief must end its first section with one of three recommendations:\n\n"
        "- **build**: the evidence is strong enough to invest in building it.\n"
        "- **pivot**: the evidence points at a different product or customer.\n"
        "- **test further**: the idea is plausible, but the riskiest assumptions are "
        "untested, so run experiments first.\n\nThe writer has to justify it from the "
        "evidence, and the critic checks that it follows.",
        "Every brief in the current evaluation recommended **test further**: interest is "
        "real, but willingness to pay is low and keeping a pantry inventory up to date is "
        "unproven.",
        ("critic_loop", "risk_analyst"),
    ),
    Term(
        "cost", "Cost (list price)", RUNS,
        "What a run would cost at Gemini's published prices, in US dollars.",
        "Each model call is priced from its tokens (per million tokens, for "
        "gemini-3.8-flash):\n\n```\ncost = uncached input × $0.75 + output (incl. thinking) "
        "× $3.75\n     + cached input × $0.075\n```\n\nA run's cost is the sum over its calls. "
        "On the free tier you actually pay $0; list price is shown so runs stay comparable "
        "and so you can see what the system would cost in production.",
        "The multi-agent run `20261013-105242-agents` cost $0.56 over 23 calls. One call, "
        "the research synthesiser thinking for 154 seconds, cost $0.11 of that.",
        ("input_tokens", "output_tokens", "model_calls"),
    ),
    Term(
        "wall_clock", "Wall clock", RUNS,
        "Real elapsed time from the start of a run to the end: how long you would wait.",
        "Measured with a timer around the whole run. It is usually less than the total model "
        "time because two agents run in parallel. It includes waiting for the API and "
        "automatic retries after rate limits, so it varies with Google's load at the time.",
        "A multi-agent run takes about 8 minutes of wall clock; a naive single prompt about "
        "25 seconds.",
        ("model_time", "pipeline"),
    ),
    Term(
        "model_time", "Model time", RUNS,
        "Seconds spent waiting for model answers, added up over every call.",
        "Each call's latency is measured, from sending the request to receiving the answer. "
        "Model time adds them up per agent. Because the research synthesiser and market "
        "analyst run at the same time, a run's total model time can be larger than its wall "
        "clock.",
        "In run `20261013-105242-agents` the model time was 572 s but the wall clock only "
        "549 s, because the two analysts overlapped.",
        ("wall_clock",),
    ),
    Term(
        "model_calls", "Model calls", RUNS,
        "How many requests were sent to the model API. Each round of tool use is one more "
        "call.",
        "A model can't run code, so using a tool takes a round trip: the model answers "
        "\"call read_interview(P01)\", the code runs it locally and sends the result back in "
        "a new request with the whole conversation so far. A single prompt is always 1 call; "
        "an agent that reads interviews or checks sources makes several. Every call is "
        "another chance for a rate limit or an error, so more calls also means less "
        "reliable.",
        "Run `20261013-105242-agents` made 23 calls: 5 by the research synthesiser, 1 each "
        "by the market and risk analysts, 2 by the writer, and 14 by the critic, which "
        "fetched sources over many tool rounds.",
        ("tool_calls", "cost"),
    ),
    Term(
        "tool_calls", "Tool calls", RUNS,
        "Requests from an agent to look something up in the data; run locally, free.",
        "Agents with tools can ask for data instead of receiving all of it up front. The "
        "code runs the lookup on the data in memory and returns the result with its "
        "citation IDs. There are three tools:\n\n"
        "- **search_interviews** (research synthesiser, critic): ranked interview turns for "
        "a query. Excluded interviews are never returned.\n"
        "- **read_interview** (research synthesiser): every turn of one interview. It "
        "refuses excluded interviews such as P06.\n"
        "- **get_sources** (critic): the exact text behind up to 20 citation IDs, so the "
        "critic can check what a citation really says.\n\n"
        "The table shows which sources each call returned, so you can see what an agent "
        "actually looked at.",
        "In run `20261013-105242-agents` the research synthesiser called read_interview 10 "
        "times, and the critic called get_sources 10 times to check the draft's "
        "citations.",
        ("model_calls", "research_synthesiser", "critic", "citation_id"),
    ),
    Term(
        "input_tokens", "Input tokens", RUNS,
        "How much text was sent to the model, in tokens (about three quarters of a word "
        "each).",
        "Everything in the request counts: instructions, data and the conversation so far. "
        "Because each tool round re-sends the whole conversation, input grows with every "
        "round. The table shows uncached input. When a request starts with the same long "
        "text as a recent one, Gemini caches that part and bills it at a tenth of the price; "
        "those cached tokens are logged separately in usage.json.",
        "The critic's first review started at 5,860 input tokens and reached 21,534 by its "
        "tenth tool round, because every round carried the sources fetched so far.",
        ("output_tokens", "cost"),
    ),
    Term(
        "output_tokens", "Output tokens", RUNS,
        "How much text the model produced, including its hidden reasoning (thinking).",
        "Gemini models reason before they answer. Those thinking tokens are never shown, but "
        "they are billed as output, at five times the input price, so they often dominate "
        "cost. The effort setting (low, medium, high) controls how much the model thinks.",
        "In one call the research synthesiser produced 27,498 output tokens, of which "
        "27,473 were thinking and only 25 were visible.",
        ("input_tokens", "cost"),
    ),
    # --- systems and agents ------------------------------------------------------------------
    Term(
        "agent", "Agent", AGENTS,
        "A role with its own instructions, inputs and output format, played by one model "
        "call (or a few, with tools).",
        "An agent here is not a separate program: it is a system prompt describing the "
        "role, a message with only the data that role may see, a required output format, "
        "and optionally tools. What makes the agents different is what each one sees. The "
        "market analyst never sees the interviews; the risk analyst never sees raw data; "
        "the critic reads the original sources rather than the analysts' summaries.",
        "The research synthesiser gets the interview tools and the EDA's interview roster, "
        "and must return a `ResearchSynthesis`: segments, insights, disagreements and "
        "willingness to pay.",
        ("research_synthesiser", "market_analyst", "risk_analyst", "brief_writer", "critic",
         "handoff"),
    ),
    Term(
        "handoff", "Hand-off", AGENTS,
        "The structured output one agent passes to the next, in a fixed format.",
        "Each agent must return JSON matching a fixed schema (a Pydantic model in "
        "`agents/contracts.py`). The model is forced to produce that shape, and the code "
        "validates it, so a malformed hand-off fails loudly instead of quietly drifting "
        "downstream. The Agents tab shows these hand-offs.",
        "Every piece of `Evidence` in a hand-off has a `source_id`, an exact `quote` and a "
        "`kind` (behaviour, stated preference or document fact).",
        ("agent", "evidence_kind"),
    ),
    Term(
        "research_synthesiser", "Research synthesiser", AGENTS,
        "The agent that reads the interviews and reports who the users are and which "
        "problems are real.",
        "Inputs: the interviews through its search and read tools, and the EDA's roster of "
        "interviews with their evidence tiers. It does not see competitors or market data. "
        "It must read every primary-tier interview in full, look for counter-evidence as "
        "hard as for support, and rate each insight's strength.",
        "Its output lists segments such as \"busy families with children\", insights such "
        "as \"inventory upkeep is a dealbreaker\", and disagreements such as whether people "
        "want to plan their week at all.",
        ("segment", "insight", "strength", "tool_calls"),
    ),
    Term(
        "market_analyst", "Market analyst", AGENTS,
        "The agent that assesses the competitors and market statistics, without seeing the "
        "interviews.",
        "Inputs: the competitor rows, the market snippets, the idea brief and the EDA's "
        "freshness and reliability checks. For each competitor it rates the overlap with "
        "PantryPal and the threat; for each statistic, whether it can back a claim; and it "
        "checks every market claim in the idea brief.",
        "It flags that the idea brief's claim \"existing recipe apps do not know what you "
        "already own\" is contradicted: FridgeChef recognises fridge photos and PantryGenie "
        "tracks a pantry inventory.",
        ("threat", "data_quality", "overlap", "claim_check"),
    ),
    Term(
        "risk_analyst", "Risk analyst", AGENTS,
        "The agent that turns both analyses into ranked assumptions and the experiments to "
        "test them.",
        "Inputs: the two analysts' hand-offs, the idea brief and the gaps the EDA found in "
        "the data. It never sees raw data and may only cite sources the analysts cited. It "
        "lists the assumptions PantryPal depends on, ranks them by risk, designs cheap "
        "tests, and suggests a recommendation.",
        "A typical riskiest assumption: \"households will keep a pantry inventory up to "
        "date\", with low confidence and high impact if wrong.",
        ("assumption", "riskiest", "experiment"),
    ),
    Term(
        "brief_writer", "Brief writer", AGENTS,
        "The agent that writes the discovery brief from the three analyses, and revises it "
        "after each critique.",
        "Inputs: the idea brief and the three hand-offs, not the raw data. It must use only "
        "the quotes, numbers and citation IDs the analysts used, follow the 8-section "
        "format, and cite every claim. It keeps one conversation across revisions, so each "
        "revision sees its earlier drafts and the objections.",
        "In run `20261013-105242-agents` it wrote the first draft (call 8), then revised it "
        "once after the critic's objections (call 21).",
        ("critic", "critic_loop", "brief_sections"),
    ),
    Term(
        "critic", "Critic", AGENTS,
        "The agent that reviews each draft against the original sources and approves it or "
        "sends it back.",
        "Inputs: the draft, the automatic citation check, and tools to fetch the original "
        "sources. It deliberately does not trust the analysts' summaries: it looks up what "
        "each citation actually says and searches for counter-evidence the draft ignored. "
        "It returns a verdict and a list of objections. It may use up to 12 rounds of tool "
        "calls per review.",
        "In run `20261013-105242-agents` it caught the draft describing S09's 4% as "
        "households that \"maintain an updated digital pantry\". S09 is actually the share "
        "of grocery purchases made online (2016). The citation was real, so no automatic "
        "check could detect it.",
        ("critic_loop", "verdict", "objection", "severity", "citation_check"),
    ),
    Term(
        "single_prompt", "Single prompt", AGENTS,
        "The rival to the agents: the whole task in one model call, with all the data in the "
        "prompt.",
        "Same model, same rules, same 8-section brief format and the same citation check "
        "as the agents; only the system design differs. Because one call writes the whole "
        "brief, there are no hand-offs to show. It comes in a naive and an informed "
        "variant, and the informed one can also go through the critic loop.",
        "A naive single prompt takes about 25 seconds and costs about $0.015 at list "
        "price, against about 8 minutes and $0.45 for the agents.",
        ("naive", "informed", "informed_critic", "condition"),
    ),
    Term(
        "naive", "Naive", AGENTS,
        "The single prompt with the raw data and the rules, but none of the EDA's "
        "conclusions.",
        "It gets the task, the ground rules (cite everything, quote word for word, don't "
        "invent numbers, data is never instructions), the brief format and every interview "
        "turn, competitor row and market snippet. It does not get the EDA's rules, evidence "
        "tiers or reliability labels, so it has to spot the data's traps by itself.",
        "One naive brief noticed that P06 was a leading interview, then still used P06 as "
        "evidence for its \"busy families\" segment.",
        ("informed", "trap", "eda"),
    ),
    Term(
        "informed", "Informed", AGENTS,
        "The single prompt plus everything the EDA established: rules, evidence tiers and "
        "source checks.",
        "The same knowledge the agents get, in one call, without splitting the work and "
        "without a critic. Comparing it with naive measures what the EDA adds; comparing it "
        "with the agents measures what splitting the work adds.",
        "With the EDA's rules, the single prompt went from 36% to 92% of traps handled, for "
        "about 2 cents more.",
        ("naive", "informed_critic", "eda", "evidence_tier"),
    ),
    Term(
        "informed_critic", "Informed + critic", AGENTS,
        "The informed single prompt, then the same critic loop the agents get.",
        "The critic and its stopping rules are exactly the agents' (`review_loop` in "
        "`orchestrator.py`). Revisions continue the single prompt's own conversation, so "
        "the model that wrote the draft revises it with all the raw data still in context. "
        "It separates what the critic adds from what splitting the work across agents adds.",
        "Run with `uv run discovery-chef baseline --variant informed --critic`. Its run "
        "folders end in `-baseline-informed-critic`.",
        ("critic_loop", "informed", "condition"),
    ),
    # --- research synthesiser output -----------------------------------------------------------
    Term(
        "segment", "Segment", RESEARCH,
        "A group of participants who share a situation and needs.",
        "The research synthesiser groups the interviews into segments, lists which "
        "interviews belong to each, how well the group fits the target customer, and what "
        "it needs. Segments describe who the users are, which is section 2 of the brief.",
        "In run `20261013-105242-agents`: \"Busy Working Families with Children\" (P01, P03, "
        "P04), fit **in**; \"Single Home Occupants / Students (Out of Target)\" (P07), fit "
        "**out**.",
        ("target_fit", "research_synthesiser"),
    ),
    Term(
        "target_fit", "Fit (target fit)", RESEARCH,
        "How well a participant matches the idea brief's target customer: in, partial or "
        "out.",
        "The target customer is \"households of two or more people who cook at home on most "
        "weeknights\". The EDA codes every participant:\n\n"
        "- **in**: matches it, e.g. P01, a working mother of two.\n"
        "- **partial**: matches part of it, e.g. P05, a freelance couple with irregular "
        "schedules.\n- **out**: does not match, e.g. P07, a student living alone who mostly "
        "eats out.\n\nA segment can be **mixed** when its members differ. Fit lowers an "
        "interview's evidence weight: out-of-target evidence counts only as contrast.",
        "P07's answers can show how non-target people behave, but not what the target "
        "customer wants.",
        ("evidence_weight", "segment"),
    ),
    Term(
        "insight", "Insight", RESEARCH,
        "One finding from the interviews, with its supporting evidence, strength and "
        "caveats.",
        "Each insight (R1, R2, ...) has a kind:\n\n"
        "- **problem**: a pain participants have.\n"
        "- **requirement**: something a solution must do.\n"
        "- **counter_evidence**: evidence against the idea.\n"
        "- **behaviour_pattern**: what people actually do today.\n\n"
        "It lists the interviews that support it, quoted evidence with citation IDs, a "
        "strength rating and caveats. Expand an insight in the Agents tab to see its "
        "evidence.",
        "R1 (problem, strong): forgotten fridge items and spoiled produce lead to recurring "
        "food waste, supported by P01, P02, P03, P05, P08 and P10, all in their own words.",
        ("strength", "own_words", "evidence_kind", "caveat"),
    ),
    Term(
        "strength", "Strength", RESEARCH,
        "How much an insight can be trusted: strong, moderate or weak.",
        "The research synthesiser rates strength from how many distinct, usable interviews "
        "support the insight in their own words, their evidence tiers, and whether the "
        "support is behaviour (stronger) or stated preference (weaker). Support resting "
        "only on templated sentences is weak.",
        "R1 (forgotten food goes off) is backed by six interviews in their own words: "
        "strong. R7 (planning a week ahead creates guilt when life gets in the way) rests "
        "on two interviews: moderate.",
        ("own_words", "evidence_kind", "templated_sentence", "evidence_tier"),
    ),
    Term(
        "own_words", "Own words", RESEARCH,
        "The interviews that support an insight in their own words, not only with a "
        "templated sentence.",
        "Some sentences appear word for word in several interviews, so they are not "
        "independent voices. For each insight, the research synthesiser lists the subset of "
        "supporting interviews whose support is not only such a sentence. A big gap between "
        "\"interviews\" and \"own words\" means the support is thinner than it looks.",
        "R4 (people reject typing in their pantry by hand) lists six supporting interviews, "
        "but only P01 and P03 in their own words: the other four only repeat \"If I need to "
        "type in my whole pantry I'll quit on day two.\"",
        ("templated_sentence", "strength"),
    ),
    Term(
        "evidence_kind", "Evidence kind", RESEARCH,
        "Whether a piece of evidence is behaviour, a stated preference, or a document fact.",
        "- **behaviour**: something the participant did. The strongest kind.\n"
        "- **stated_preference**: an opinion, wish or prediction, such as \"I would pay "
        "for that\". People are poor at predicting their own behaviour, so it is weaker.\n"
        "- **document_fact**: a competitor row or market snippet.\n\n"
        "Keeping these apart is one of the ground rules every agent follows.",
        "Behaviour: P01 \"bought a big bag of spinach for a recipe I never made. It went "
        "slimy in the drawer\". Stated preference: \"A few euros a month, maybe, if it "
        "clearly saves me money on groceries.\"",
        ("strength", "insight"),
    ),
    Term(
        "caveat", "Caveat", RESEARCH,
        "A limitation that qualifies an insight.",
        "Caveats say why an insight might be weaker or narrower than it looks: a small "
        "number of interviews, templated wording, partial target fit, or contradicting "
        "evidence.",
        "\"Support comes mostly from one templated sentence repeated in five interviews.\"",
        ("insight", "strength"),
    ),
    # --- market analyst output -----------------------------------------------------------------
    Term(
        "threat", "Threat", MARKET,
        "How much a competitor endangers PantryPal: high, medium or low.",
        "The market analyst judges threat from how much of PantryPal's promise the "
        "competitor already covers, its price, and how current its data is.",
        "MealLoop (weekly plans, grocery list, family sharing, EUR 6.99/month) overlaps "
        "much of PantryPal and was rated the only **high** threat in run "
        "`20261013-105242-agents`.",
        ("overlap", "data_quality", "market_analyst"),
    ),
    Term(
        "data_quality", "Data quality (competitor row)", MARKET,
        "Whether a competitor row can be trusted: current, stale or unsourced.",
        "Rated by the market analyst from the EDA's freshness check, which measures days "
        "since the row was last verified, counted back from the research date "
        "(2026-09-14): more than 180 days is aging, more than 365 days is stale. A row "
        "without a source URL is unsourced.",
        "PlanPlate was last verified 678 days before the research date (stale). WeekWise "
        "has no source URL (unsourced).",
        ("research_date", "threat"),
    ),
    Term(
        "overlap", "Overlap", MARKET,
        "Which parts of PantryPal's promise a competitor already offers.",
        "Chosen from six capabilities: knows_inventory (knows what you own), weekly_plan, "
        "shopping_list, household_sharing, waste_reduction and budget_focus.",
        "PantryGenie (barcode scanning, expiry alerts, shopping list) overlaps on "
        "knows_inventory, waste_reduction and shopping_list.",
        ("threat",),
    ),
    Term(
        "claim_check", "Claim check", MARKET,
        "A verdict on one of the idea brief's claims: supported, partly supported, "
        "unsupported or contradicted.",
        "The market analyst quotes each claim the idea brief makes about the market or "
        "existing apps, and says what the data says about it, citing the sources.",
        "\"Existing recipe apps give ideas but do not know what you already own\": "
        "**contradicted**, citing C:FridgeChef (photo recognition), C:PantryGenie (pantry "
        "inventory) and C:ZeroWaste Kitchen (leftover recipes).",
        ("market_analyst",),
    ),
    # --- risk analyst output ---------------------------------------------------------------
    Term(
        "assumption", "Assumption", RISK,
        "Something PantryPal needs to be true, with the evidence for and against it.",
        "Each assumption (A1, A2, ...) has a type:\n\n"
        "- **desirability**: do people want it?\n"
        "- **usability**: can they use it, e.g. keep an inventory current?\n"
        "- **viability**: will they pay, and can it compete?\n"
        "- **feasibility**: can it be built?\n\n"
        "It also has a **confidence** (how sure the evidence lets us be that it holds: low, "
        "medium or high) and an **impact if wrong** (low, medium or high).",
        "A3: \"Target households are willing to pay a recurring monthly subscription\": "
        "viability, confidence low, impact if wrong high.",
        ("riskiest", "experiment"),
    ),
    Term(
        "riskiest", "Rank (riskiest assumptions)", RISK,
        "The assumptions ordered by risk: rank 1 is the one most likely to sink the product.",
        "An assumption is risky when confidence is low and the impact if wrong is high. The "
        "risk analyst ranks them, and the experiments target the top of the list first.",
        "In run `20261013-105242-agents`, rank 1 was A1 (usability): \"Households will "
        "maintain an accurate digital pantry inventory over time\", confidence low, impact "
        "high.",
        ("assumption", "experiment"),
    ),
    Term(
        "experiment", "Experiment", RISK,
        "A concrete test that would settle one or more of the riskiest assumptions.",
        "Each experiment (E1, E2, ...) names the assumptions it tests, a hypothesis, a "
        "method (who, what, how many), a success metric and a cost. Sample sizes and "
        "thresholds are proposals, not findings, so the brief marks them [UNSUPPORTED].",
        "E1 tests A1: recruit 20 target households and give them a prototype with three "
        "ways to log their pantry, for a week.",
        ("success_metric", "riskiest", "unsupported_tag"),
    ),
    Term(
        "success_metric", "Success metric", RISK,
        "The result that would count as the experiment passing, and so change the decision.",
        "A good success metric is measurable and decided before the test, so the result "
        "cannot be argued away afterwards.",
        "E1: \"At least 14 of 20 households (70%) keep their inventory updated through "
        "Day 7 with average logging time under 2 minutes per session.\"",
        ("experiment",),
    ),
    # --- critic loop -------------------------------------------------------------------------
    Term(
        "critic_loop", "Critic loop", CRITIC,
        "The cycle of the critic reviewing a draft and the writer revising it, until it "
        "stops.",
        "After the first draft, the critic reviews it. If it isn't approved, the writer "
        "revises and the critic reviews again. The loop stops with one of three outcomes:\n\n"
        "- **approved**: the critic approves *and* the automatic citation check passes. A "
        "model's approval never overrides a failed check.\n"
        "- **revision_limit**: the cap of revisions (2 by default) was reached.\n"
        "- **stalled**: a revision did not reduce the number of blocker and major "
        "objections, so it stops rather than going round in circles.\n\n"
        "Single-prompt runs without the critic show n/a.",
        "All three multi-agent runs in the current evaluation ended **approved**, after 1, "
        "2 and 2 review rounds.",
        ("critic", "verdict", "severity", "citation_check"),
    ),
    Term(
        "verdict", "Verdict", CRITIC,
        "The critic's decision on a draft: approve or revise.",
        "The critic may only approve when no blocker or major objection remains. Minor "
        "objections can remain in an approved brief. Approval alone does not end the loop: "
        "the automatic citation check must also pass.",
        "Run `20261013-105242-agents`: round 0 **revise** (1 blocker, 4 major, 3 minor); "
        "round 1 **approve** (no objections left).",
        ("objection", "severity", "critic_loop"),
    ),
    Term(
        "objection", "Objection", CRITIC,
        "One specific problem the critic found in a draft, with the text at issue and how to "
        "fix it.",
        "Each objection has a severity, a category, the section of the brief, an excerpt "
        "copied exactly from the brief, the problem, and the fix. The writer receives every "
        "objection and must fix them all.\n\n"
        "Categories: unsupported_claim, wrong_citation, misquote, invented_number, "
        "excluded_source, overclaim, missing_content, contradiction, unclear.",
        "**blocker** (unsupported_claim, section 8): the excerpt \"Market claim that 4% of "
        "households maintain an updated digital pantry\". Problem: S09 is the share of "
        "grocery purchases made online, not pantry maintenance. *Fix:* describe S09's "
        "actual claim.",
        ("severity", "verdict", "revision_diff"),
    ),
    Term(
        "severity", "Severity", CRITIC,
        "How serious an objection is: blocker, major or minor.",
        "- **⛔ blocker**: factually wrong, invented, or relies on excluded evidence.\n"
        "- **⚠️ major**: an overclaim or an unsupported claim that matters to the "
        "decision.\n- **ℹ️ minor**: wording, clarity or a small omission.\n\n"
        "Blockers plus majors are the \"serious\" objections: the critic can't approve while "
        "any remain, and the loop stalls if a revision doesn't reduce them.",
        "Blocker: describing S09's 4% as households keeping a digital pantry (it is online "
        "grocery share). Major: citing P02 for a strict 30-minute cooking limit when P02 "
        "only says they cook \"pasta or something quick\".",
        ("objection", "critic_loop"),
    ),
    Term(
        "revision_diff", "What the revisions changed", CRITIC,
        "The lines that differ between the first draft and the final brief.",
        "Shown as a diff: lines starting with − were in the first draft and were removed or "
        "changed; lines starting with + are in the final brief. It shows concretely what the "
        "critic's objections led the writer to change.",
        "`- Market claim that 4% of households maintain an updated digital pantry: "
        "Unsupported ...`\n\n"
        "`+ Share of grocery purchases made online: 4% (2016): This snippet is stale ... "
        "and measures online grocery purchasing rather than digital pantry maintenance "
        "[S09].`",
        ("objection", "critic_loop"),
    ),
    # --- citations and checks ----------------------------------------------------------------
    Term(
        "citation_id", "Citation ID", CHECKS,
        "The bracketed reference after a claim that names its exact source.",
        "| Format | Points to | Example |\n|---|---|---|\n"
        "| `P02:t4` | interview P02, turn 4 (one question and answer) | [P02:t4] |\n"
        "| `P02` | the whole interview, only for facts about the person | [P07] |\n"
        "| `C:<name>` | a row of competitors.csv | [C:MealLoop] |\n"
        "| `S01`-`S09` | a market snippet, by position in market_snippets.json | [S05] |\n"
        "| `idea_brief` | the idea brief, only for what it claims | [idea_brief] |\n\n"
        "Internal IDs (EDA findings F01-F19, insights R1, assumptions A1, experiments E1) "
        "are not sources and must never be cited.",
        "\"Couples who both shop buy the same items twice [P02:t4]\": the claim is backed by "
        "turn 4 of interview P02. Use \"Trace a citation\" to read it.",
        ("trace_citation", "citation_check", "unsupported_tag"),
    ),
    Term(
        "trace_citation", "Trace a citation", CHECKS,
        "Pick any citation ID in the brief and read the original source text behind it.",
        "The list holds every distinct citation ID in the final brief. Selecting one shows "
        "the exact source as the agents saw it: the interviewer's question and the "
        "participant's answer, the competitor row, or the snippet with its source. Use it to "
        "check whether a claim really follows from its source.",
        "Select `S08` and you see \"Households that would pay for automated meal planning: "
        "97%, App Trends Blog (2025)\": a blog, not research, which is why careful briefs "
        "don't use it as fact.",
        ("citation_id", "misrepresentation"),
    ),
    Term(
        "citation_check", "Automated citation check", CHECKS,
        "A rule-based check of a brief's citations, quotes, numbers and sections; no model "
        "involved.",
        "It runs on every draft (the critic sees the report) and on every final brief, "
        "including the single prompt's. **Blocking** issues fail the check:\n\n"
        "- citation IDs that don't exist, or internal IDs cited as sources\n"
        "- citations of excluded interviews used as evidence\n"
        "- quotes not found word for word in the cited source\n"
        "- dates not found in the data\n"
        "- missing required sections\n\n"
        "It also reports, without failing: numbers found in no source, claim lines without "
        "a citation, and unusable market snippets cited without a caveat. It cannot tell "
        "whether a source supports a claim; that is the critic's and the judge's job.",
        "One draft wrote \"2004\" for the research year \"2024\"; the check flagged the date "
        "as not found in the data, which the critic had missed.",
        ("blocking_issue", "claim_coverage", "verified_quote", "critic"),
    ),
    Term(
        "blocking_issue", "Blocking issue", CHECKS,
        "A citation-check problem serious enough to fail the brief.",
        "Blocking issues: unknown citation IDs, citations of excluded interviews, quotes not "
        "found word for word, dates not in the data, and missing sections. A brief passes "
        "only with zero blocking issues, and the critic loop can't end as approved while "
        "any remain, whatever the critic says.",
        "Citing `[P99:t4]` (there is no P99) or quoting \"we always waste food\" when no "
        "participant said those words.",
        ("citation_check", "critic_loop"),
    ),
    Term(
        "claim_coverage", "Claim coverage", CHECKS,
        "The share of claim lines that carry a citation or an [UNSUPPORTED] flag.",
        "In sections 2 to 7 of the brief, every line of 12 or more words counts as a claim "
        "line. Coverage is the share of those lines with at least one citation ID or "
        "[UNSUPPORTED]. 100% means no claim is left unsourced and unflagged.",
        "A brief with 50 claim lines, 49 of them cited: 98% coverage.",
        ("citation_check", "unsupported_tag"),
    ),
    Term(
        "verified_quote", "Verified quote", CHECKS,
        "A quotation in the brief that was found word for word in the source it cites.",
        "Text inside double quotes, four words or longer, is checked against the cited "
        "sources (ignoring case and spacing). A quote that isn't found is a misquote and a "
        "blocking issue. More verified quotes means more of the brief rests on participants' "
        "actual words.",
        "\"We bought basil twice in one week because each of us thought we were out\" "
        "[P02:t4] is verified: P02 said exactly that.",
        ("citation_check",),
    ),
    Term(
        "unsupported_tag", "[UNSUPPORTED]", CHECKS,
        "A flag on a claim that has no source, so readers don't mistake it for evidence.",
        "The brief format requires a claim without support either to go into section 8 "
        "(unsupported or weak claims) or to carry [UNSUPPORTED]. Experiment sample sizes and "
        "success thresholds are proposals, so they carry it too.",
        "\"Recruit 10 households for a one-week test [UNSUPPORTED].\"",
        ("citation_id", "brief_sections"),
    ),
    Term(
        "brief_sections", "Brief sections", CHECKS,
        "The 8 sections every brief must have, in this order.",
        "1. Recommendation\n2. Who the users are\n3. Problems that are real\n4. What the "
        "evidence says\n5. Competitors and market\n6. Risks and open assumptions\n7. What "
        "to test next\n8. Unsupported or weak claims\n\nA missing section is a blocking "
        "issue. The fixed format makes briefs from different systems directly comparable.",
        "Section 8 is where a careful brief lists the 97% blog statistic, explaining why it "
        "is not used.",
        ("citation_check", "recommendation"),
    ),
    # --- evaluation ----------------------------------------------------------------------------
    Term(
        "condition", "System (condition)", EVAL,
        "One of the systems being compared; each row of the comparison table is one.",
        "| Condition | What it is | Compared with it, it isolates |\n|---|---|---|\n"
        "| Single prompt (naive) | one call, raw data | (baseline) |\n"
        "| Single prompt + EDA rules | one call plus the EDA's findings | what the EDA "
        "adds |\n"
        "| Single prompt + EDA + critic | the above, then the critic loop | what the critic "
        "adds without agents |\n"
        "| Agents, before critic | the multi-agent first draft | what splitting the work "
        "adds |\n"
        "| Agents, after critic | the final multi-agent brief | what the critic adds to "
        "agents |\n\n"
        "\"Before critic\" briefs are not separate runs: every run with a critic saves its "
        "first draft, which is scored as if the run had stopped there, with the critic's "
        "cost and time removed.",
        "Agents before critic: 0.75 quality; after critic: 0.88. The difference is the "
        "critic's contribution.",
        ("naive", "informed", "informed_critic", "n_briefs"),
    ),
    Term(
        "n_briefs", "n", EVAL,
        "How many briefs were scored for a condition; every other number is their average.",
        "Only finished runs on the same model and the same code version count. With n = 3, "
        "one unusual brief moves the average a lot, so small differences between conditions "
        "may be noise.",
        "Quality per brief ranges from about 0.6 to 0.97 within a single condition, which is "
        "wider than the gap between informed (0.86) and agents (0.88).",
        ("fingerprint", "quality_vs_cost"),
    ),
    Term(
        "quality_index", "Quality (0-1)", EVAL,
        "The headline score: the average of traps handled, faithfulness and the criteria, "
        "each on a 0-1 scale.",
        "Computed per brief, then averaged:\n\n```\nquality = (traps handled + faithfulness "
        "+ (criteria − 1) / 4) / 3\n```\n\nIt is only used to order the systems. Different "
        "weaknesses can give the same score, so always look at the three parts too.",
        "Naive: (0.361 traps + 0.917 faithfulness + 0.817 criteria) / 3 = **0.70**.",
        ("trap", "misrepresentation", "criteria"),
    ),
    Term(
        "trap", "Traps handled", EVAL,
        "The share of 12 known problems in this data that the brief dealt with correctly.",
        "The EDA established 12 traps a careful brief must handle:\n\n"
        "T01 leading interview (P06) excluded · T02 templated answers discounted · T03 "
        "target fit distinguished · T04 fit is not the same as pain · T05 willingness to pay "
        "kept honest · T06 inventory upkeep named as a key risk · T07 planning itself is "
        "contested · T08 \"stop arguing\" weakly supported · T09 competitors already know "
        "what you own · T10 stale competitor rows caveated · T11 unreliable market figures "
        "not used as fact · T12 limits of the evidence stated\n\n"
        "A trap counts as handled only if the judge quotes the brief to prove it, the quote "
        "is found word for word, and the citation check doesn't veto it (for example, P06 "
        "cited as evidence fails T01 whatever the judge says).",
        "Naive briefs handled 36% (about 4 of 12); briefs with the EDA's rules 92%.",
        ("quality_index", "judge", "eda"),
    ),
    Term(
        "misrepresentation", "Misrepresented sources", EVAL,
        "Claims, on average per brief, that say something their cited source doesn't. "
        "Lower is better.",
        "The judge reads the brief and all the raw sources, and lists each claim that "
        "misrepresents what it cites. Only items whose quoted text is found in the brief "
        "count. Each one costs a quarter of the brief's **faithfulness** score (0 errors: "
        "1.0; 1: 0.75; 4 or more: 0). Citation IDs and quote checks can't catch this kind "
        "of error, because the ID is real; only the critic and the judge can.",
        "\"4% of households maintain an updated digital pantry [S09]\", when S09 is the "
        "share of grocery purchases made online.",
        ("quality_index", "judge", "critic"),
    ),
    Term(
        "criteria", "Criteria (1-5)", EVAL,
        "The judge's average over five scores from 1 to 5: completeness, evidence, "
        "calibration, actionability and clarity.",
        "| | Criterion | Asks |\n|---|---|---|\n"
        "| C1 | Completeness | Are all six questions answered with substance? |\n"
        "| C2 | Evidence grounding | Is every claim cited, with evidence strength stated? "
        "Any misrepresentation caps it at 3. |\n"
        "| C3 | Calibration | Does confidence match the evidence, without overclaiming? |\n"
        "| C4 | Actionability | Is the recommendation clear, are tests concrete (who, how "
        "many, metric, decision)? |\n"
        "| C5 | Clarity | Concise and easy for a product team to act on? |\n\n"
        "Each score uses written descriptions of a 1, a 3 and a 5, and the judge lists the "
        "brief's weaknesses before scoring. These scores are not verified against the brief "
        "the way traps are, so they are the least objective part; hand-scoring in "
        "`outputs/eval/blind/` checks them.",
        "In the rubric's words, a 3 on C4 (actionability) means \"Clear recommendation; "
        "tests named but missing a sample, a success metric or the decision they "
        "inform.\"",
        ("quality_index", "judge"),
    ),
    Term(
        "judge", "Judge", EVAL,
        "A stronger model that scores every brief, without knowing which system wrote it.",
        "The judge (`gemini-3.1-pro-preview`) reads one brief at a time plus all the raw "
        "research data, without the EDA's labels. It lists weaknesses, misrepresentations, "
        "which traps are handled and the five criteria. Its claims are verified: a trap or "
        "misrepresentation only counts if the text it quotes is really in the brief. "
        "Verdicts are cached by brief text, so re-scoring is free and reproducible.",
        "If the judge says a brief handles T02 but quotes a sentence the brief doesn't "
        "contain, T02 counts as not handled.",
        ("trap", "misrepresentation", "criteria", "model"),
    ),
    Term(
        "fingerprint", "Code fingerprint", EVAL,
        "A short hash of the code that shapes prompts and checks; only runs with the same "
        "fingerprint are compared.",
        "Each run records a 12-character hash of the agent prompts, the orchestrator, the "
        "citation checker, the model clients and the EDA profile. When any of these change, "
        "new runs get a new fingerprint, and the evaluation stops mixing them with old ones, "
        "so a prompt change can't silently blend two versions of a system.",
        "The current evaluation compares runs with fingerprint `cc37932e263b`; 16 runs made "
        "with other code or models were left out.",
        ("n_briefs", "model"),
    ),
    Term(
        "quality_vs_cost", "Quality against cost chart", EVAL,
        "Each brief's quality index plotted against what it cost.",
        "- Up is better quality; right is more expensive. The best place is top-left.\n"
        "- The cost axis is logarithmic: each gridline is 10 times the previous one.\n"
        "- Small marks are single briefs; large labelled marks are condition averages.\n"
        "- Blue is a single prompt, orange is agents; hollow is without the improvement "
        "(naive, agents before critic), filled is with it. A diamond is the single prompt "
        "with the critic.\n\n"
        "The spread of the small marks shows how much briefs from the same system vary.",
        "\"Single prompt + EDA rules\" sits almost as high as \"Agents, after critic\" but "
        "far to the left: similar quality for about a fourteenth of the cost.",
        ("quality_index", "cost", "condition"),
    ),
    # --- evidence and the EDA ------------------------------------------------------------------
    Term(
        "eda", "EDA (exploratory data analysis)", EDA,
        "Phase 1: plain Python code that profiles the data and decides what can be trusted, "
        "before any model sees it.",
        "The EDA (`discovery-chef eda`) weights each interview, finds templated answers and "
        "leading questions, checks how current each competitor row is and how reliable each "
        "statistic is, and writes 19 findings. Each finding ends with a rule for the agents "
        "(\"so the agent will ...\"). The result, `outputs/eda/evidence_profile.json`, is "
        "what the informed prompt and the agents receive.",
        "Finding F04: P06 departs from the interview guide on 10 of 10 questions and 9 are "
        "leading, \"so the agent will give P06 zero weight\".",
        ("evidence_tier", "templated_sentence", "leading_question", "informed"),
    ),
    Term(
        "evidence_tier", "Evidence tier", EDA,
        "How much an interview counts as evidence: primary, supporting, contrast only, or "
        "excluded.",
        "Set from the interview's evidence weight:\n\n"
        "| Tier | Weight | Interviews |\n|---|---|---|\n"
        "| primary | 0.8 or more | P01, P02, P09 |\n"
        "| supporting | 0.4 to 0.8 | P03, P04, P05, P08, P10 |\n"
        "| contrast only | above 0, below 0.4 | P07 |\n"
        "| excluded | 0 | P06 |\n\n"
        "Search results show each passage's tier, and excluded interviews are never "
        "returned.",
        "P07 (a student living alone) is contrast only: useful to show how non-target "
        "people behave, not as evidence of what the target customer wants.",
        ("evidence_weight", "target_fit", "eda"),
    ),
    Term(
        "evidence_weight", "Evidence weight", EDA,
        "A 0-1 score for how much one interview counts, from its quality and its target fit.",
        "```\nevidence weight = quality × fit factor\n```\n\n"
        "- Quality starts at 1 and loses 0.3 per major and 0.1 per minor issue affecting "
        "the whole interview (such as a participant contradicting themselves). An interview "
        "where at least half the questions are leading gets quality 0.\n"
        "- Fit factor: in 1.0, partial 0.5, out 0.25.",
        "P03: one major issue (an internal contradiction), so quality 0.7 × fit 1.0 = 0.7. "
        "P05: no issues, but partial fit, so 1.0 × 0.5 = 0.5.",
        ("evidence_tier", "target_fit", "leading_question"),
    ),
    Term(
        "leading_question", "Leading question", EDA,
        "A question that suggests the answer it wants, so the reply says little about what "
        "the participant really thinks.",
        "The EDA flags four patterns: a question opening with \"Don't you\" or \"Wouldn't "
        "it\"; a tag at the end such as \"..., wouldn't you?\" or \"..., right?\"; a "
        "presumption such as \"I imagine\", \"I bet\", \"must be\" or \"surely\"; and "
        "loaded words such as \"nightmare\", \"amazing\", \"struggle\" or "
        "\"definitely\". An interview where at least half the questions are leading is "
        "excluded from evidence.",
        "P06: \"You'd definitely pay for something that saved you that much time, wouldn't "
        "you?\" → \"Probably, yes. Hmm, yes. Why not.\" 9 of P06's 10 questions are "
        "leading, so it is excluded.",
        ("evidence_tier", "trap"),
    ),
    Term(
        "templated_sentence", "Templated sentence", EDA,
        "A sentence that appears word for word in several interviews, so it isn't an "
        "independent voice.",
        "The EDA finds answer sentences of four or more words repeated across interviews. "
        "Real people rarely use identical sentences, so agreement that rests on them is "
        "weaker than it looks. Search results flag them on each passage.",
        "\"Setup has to be fast. If I need to type in my whole pantry I'll quit on day "
        "two.\" appears in P02, P05, P07, P08 and P10.",
        ("own_words", "strength", "trap"),
    ),
    Term(
        "research_date", "Research date", EDA,
        "The date of the last interview, 2026-09-14, used as \"today\" for all freshness "
        "checks.",
        "Freshness is measured against the research date, not the real clock, so the EDA "
        "gives identical results whenever it runs.",
        "PlanPlate, last verified 2024-11-05, is 678 days older than the research date: "
        "stale.",
        ("data_quality",),
    ),
)

TERMS_BY_SLUG = {term.slug: term for term in TERMS}
