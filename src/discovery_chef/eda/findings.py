"""EDA findings, each ending in the rule it sets for the agents ("So the agent will ...").

Counts and ID lists are read from the computed profile, so they update when the data or
the coding changes. Illustrative examples, and the analyst judgements in F14 and F19, are
written by hand. Text in double quotes inside a finding is a verbatim quote from the data;
tests/test_eda.py checks every one. Single quotes mark terms, not quotes.
Phase 2 loads the rules into the agents' instructions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from discovery_chef.eda.annotations import IDEA_CLAIMS, INTERVIEW_CODING
from discovery_chef.eda.codebook import CAPABILITIES

if TYPE_CHECKING:
    from discovery_chef.eda.profile import EdaProfile

# A problem theme counts as well supported when at least this many interviews raise it in
# their own words (not only through a templated sentence).
MIN_OWN_WORDS_INTERVIEWS = 3

QUESTIONS = {
    "Q1": "Who took part, and how well do they match the target customer?",
    "Q2": "How strong is the evidence in each interview?",
    "Q3": "Which themes recur, and where do participants disagree?",
    "Q4": "How trustworthy and current are the competitor entries and market snippets?",
    "Q5": "What does the data not tell us that a discovery brief needs?",
}


@dataclass(frozen=True)
class Finding:
    id: str
    question: str
    title: str
    finding: str
    evidence: tuple[str, ...]  # interview IDs, competitor names or snippet IDs
    so_the_agent_will: str
    headline: bool = False  # one of the findings that matter most for the presentation

    def __post_init__(self):
        object.__setattr__(self, "evidence", tuple(dict.fromkeys(self.evidence)))

    def to_dict(self) -> dict:
        return asdict(self)


def join_ids(ids) -> str:
    ids = list(ids)
    if len(ids) <= 1:
        return "".join(ids)
    return f"{', '.join(ids[:-1])} and {ids[-1]}"


def build_findings(p: EdaProfile) -> list[Finding]:
    m = p.metrics.set_index("interview_id")
    support = p.theme_support.set_index("theme")
    comp = p.competitors.set_index("competitor")
    snip = p.snippets.set_index("snippet_id")
    coding = INTERVIEW_CODING

    def where(column, value, frame=m):
        return sorted(frame.index[frame[column] == value])

    def themed(theme):
        return list(support.loc[theme, "interviews"])

    findings: list[Finding] = []
    add = findings.append

    # Q1 - participants and target fit ---------------------------------------------------
    fit_in, fit_partial, fit_out = where("target_fit", "in"), where("target_fit", "partial"), \
        where("target_fit", "out")
    add(Finding(
        "F01", "Q1", "Only part of the sample is the target customer",
        f"{len(fit_in)} of {len(m)} participants meet both target criteria (two or more "
        f"people, cooking at home most weeknights): {join_ids(fit_in)}. {join_ids(fit_partial)} "
        f"are partial fits (several people, but irregular or separate cooking) and "
        f"{join_ids(fit_out)} is outside the target (lives alone, cooks about once a week).",
        tuple(m.index),
        "So the agent will tag every interview-based claim with the segment it comes from, "
        "never generalise from out-of-target interviews to the target customer, and label "
        "partial-fit evidence as coming from an adjacent segment.",
        headline=True,
    ))

    usable = m[m["evidence_tier"] != "excluded"]
    segments = {
        t: sorted(usable.index[usable["household_type"] == t])
        for t in ("family_with_children", "couple_no_children", "flatmates", "single")
    }
    add(Finding(
        "F02", "Q1", "No segment has enough interviews to generalise",
        f"After excluding unusable interviews, the sample splits into families with children "
        f"({join_ids(segments['family_with_children'])}), couples without children "
        f"({join_ids(segments['couple_no_children'])}), flatmates "
        f"({join_ids(segments['flatmates'])}) and one person living alone "
        f"({join_ids(segments['single'])}). The largest segment has "
        f"{max(len(v) for v in segments.values())} interviews.",
        tuple(usable.index),
        "So the agent will report support as interview counts within a segment "
        "(for example '3 of 4 couples'), never as percentages, and state the sample size "
        "next to every segment-level claim.",
    ))

    no_pain = themed("no_pain")
    no_pain_in_target = [i for i in no_pain if m.loc[i, "target_fit"] == "in"]
    families = segments["family_with_children"]
    fatigued = [i for i in families if i in themed("decision_fatigue")]
    add(Finding(
        "F03", "Q1", "Being in the target is not the same as having the problem",
        f"{join_ids(no_pain_in_target)} meets the target definition but reports little or no "
        f"problem with dinner today and would not pay. By contrast, {len(fatigued)} of "
        f"{len(families)} usable families with children ({join_ids(fatigued)}) describe "
        f"deciding what to cook as a burden, and {join_ids(themed('duplicate_purchases'))} "
        f"(households where several people shop) report duplicate purchases.",
        tuple(sorted(set(no_pain) | set(fatigued) | set(themed("duplicate_purchases")))),
        "So the agent will keep 'in the target' separate from 'has the problem', and list "
        "the target definition itself as an assumption to test.",
    ))

    # Q2 - evidence strength --------------------------------------------------------------
    shared = p.shared_sentences
    excluded = where("evidence_tier", "excluded")
    for iid in excluded:
        row = m.loc[iid]
        opening = p.dataset.interviews[iid].turns[0].answer_sentences
        copied_from = sorted(
            {other for ids in shared.loc[shared["sentence"].isin(opening), "interviews"]
             for other in ids} - {iid}
        )
        add(Finding(
            "F04", "Q2", f"{iid} is not usable evidence",
            f"{iid} departs from the shared interview guide on {row.off_guide_questions} of "
            f"{len(p.dataset.interviews[iid].turns)} questions; {row.leading_questions} are "
            f'leading (for example "Wouldn\'t it be amazing if an app just planned all your '
            f'meals automatically?") and {row.acquiescent_answers} answers simply agree. Its '
            f"opening answer is a word-for-word copy of {join_ids(copied_from)}.",
            (iid, *copied_from),
            f"So the agent will give {iid} zero weight: it will not cite {iid} for any "
            "customer claim and will mention it only as a research-method problem.",
            headline=True,
        ))

    setup = support.loc["fast_setup"]
    add(Finding(
        "F05", "Q2", "Templated answers inflate how often themes appear",
        f"{len(shared)} answer sentences appear word for word in two or more interviews; on "
        f"average {m['templated_sentence_ratio'].mean():.0%} of an interview's sentences are "
        f'shared with another interview. The most common requirement, "Setup has to be fast. '
        f'If I need to type in my whole pantry I\'ll quit on day two.", appears in '
        f"{setup.raw_interviews} interviews and never in a participant's own words.",
        tuple(setup.interviews),
        "So the agent will count support by distinct interviews, show raw and "
        "evidence-weighted counts side by side, flag templated quotes, and treat theme "
        "frequencies as upper bounds rather than independent agreement.",
        headline=True,
    ))

    contradicted = sorted(
        iid for iid, c in coding.items()
        if any(i.kind in ("internal_contradiction", "attribution_inconsistency",
                          "internal_inconsistency") for i in c.issues)
    )
    major = [i for i in contradicted if m.loc[i, "major_issues"] > 0]
    add(Finding(
        "F06", "Q2", "Several transcripts contradict themselves",
        f"{join_ids(contradicted)} contain statements that conflict with each other "
        f'(major in {join_ids(major)}). P03 calls planning "my favourite part of the week" '
        f'but says "Deciding is exhausting"; P04\'s persona is a father who mentions both '
        f'"my wife" and "my husband".',
        tuple(contradicted),
        "So the agent will not cite a contradicted statement on its own: when it uses one of "
        "these interviews it will show the conflicting quote next to it and lower its "
        "confidence.",
    ))

    presupposing = int(m.loc[m["evidence_tier"] != "excluded", "presupposing_questions"].max())
    add(Finding(
        "F07", "Q2", "Past behaviour is stronger evidence than stated opinion",
        'Questions about last Tuesday and "the last time this went wrong" produce concrete '
        "episodes (spinach in P01, basil bought twice in P02, chicken bought twice in P04, "
        "the holiday fridge in P08). Questions about trust and payment ask people to "
        f"predict their own behaviour. The guide itself presupposes a problem in "
        f'{presupposing} questions ("most frustrating part", "went wrong").',
        ("P01", "P02", "P04", "P08"),
        "So the agent will prefer past-behaviour quotes as evidence that a problem is real, "
        "label requirements and willingness to pay as stated intent, and treat answers about "
        "frustration as prompted rather than spontaneous.",
    ))

    wtp = {c.interview_id: c.wtp for c in coding.values()}

    def wtp_ids(category):
        return sorted(i for i, w in wtp.items() if w.category == category)

    s05 = p.dataset.snippets["S05"]
    add(Finding(
        "F08", "Q2", "Willingness to pay is low and conditional",
        f"{len(wtp_ids('none'))} would not pay ({join_ids(wtp_ids('none'))}). "
        f"{join_ids(sorted(wtp_ids('low_conditional') + wtp_ids('free_or_conditional')))} "
        f"would pay "
        f"a few euros only if the app clearly saves money or reduces waste (or accept a free "
        f"version with ads). {join_ids(wtp_ids('low'))} caps it at about EUR 6. "
        f"{join_ids(wtp_ids('high_outlier'))}'s EUR 30/month is anchored on one holiday "
        f'incident, and {join_ids(wtp_ids("unusable"))}\'s "yes" was led. The market median '
        f"in S05 is {s05.stat}.",
        tuple(sorted(wtp)) + ("S05",),
        "So the agent will report willingness to pay as a range with its conditions "
        "attached, leave the outlier out of any typical figure, and never claim that "
        "willingness to pay is validated.",
    ))

    injection = p.injection_hits
    add(Finding(
        "F09", "Q2", "No instruction-like text was found in the data",
        f"A scan of every file for instruction-like phrases found {len(injection)} matches.",
        (),
        "So the agent will still pass all source text to the model as quoted data inside "
        "clear delimiters and will never follow instructions that appear in it.",
    ))

    # Q3 - themes and disagreements ---------------------------------------------------------
    problems = support[(support["kind"] == "problem")
                       & (support["non_templated_interviews"] >= MIN_OWN_WORDS_INTERVIEWS)]
    problems = problems.sort_values("weighted_support", ascending=False)
    def problem_line(row) -> str:
        own_words = [i for i in row.own_words_interviews if i not in excluded]
        templated_only = [i for i in row.interviews
                          if i not in row.own_words_interviews and i not in excluded]
        line = f"{row.label.lower()} (own words: {join_ids(own_words)}"
        if templated_only:
            line += f"; templated sentence only: {join_ids(templated_only)}"
        return line + f"; weighted {row.weighted_support})"

    problem_text = "; ".join(problem_line(row) for row in problems.itertuples())
    add(Finding(
        "F10", "Q3",
        f"{len(problems)} problems are backed by several interviews in their own words",
        f"Problems raised by at least {MIN_OWN_WORDS_INTERVIEWS} interviews in their own words, "
        f"ranked by evidence-weighted support: {problem_text}.",
        tuple(sorted({i for ids in problems["own_words_interviews"] for i in ids}
                     - set(excluded))),
        "So the agent will build problem statements from these themes first, citing the "
        "interviews for each and giving the weighted support, and will not cite excluded "
        "interviews even when they mention the theme.",
        headline=True,
    ))

    caps = p.capabilities
    inventory = sorted(caps.index[caps["knows_inventory"] == 1])
    add(Finding(
        "F11", "Q3", "The core mechanic runs into the strongest barrier",
        f"PantryPal only works if it knows what is in the fridge, yet "
        f"{setup.raw_interviews} interviews ({join_ids(setup.interviews)}) say they will quit "
        f"if they have to type in their pantry, and P05 already gave up on a meal-planning "
        f"app within a week. Competitors {join_ids(inventory)} show existing low-effort "
        f"input methods (photo recognition, barcode scanning).",
        tuple(setup.interviews) + ("P05",) + tuple(inventory),
        "So the agent will make 'households will keep a pantry inventory up to date' the "
        "riskiest assumption, and will propose testing low-effort input before the planner "
        "itself.",
        headline=True,
    ))

    resist, enjoys, control = (themed("planning_resistance"), themed("enjoys_planning"),
                               themed("user_control"))
    add(Finding(
        "F12", "Q3", "Planning itself is contested",
        f"Rejected planning ahead or gave up on a planning app: {join_ids(resist)} "
        f'("A plan I don\'t follow feels like failure"). Enjoys planning and would not hand '
        f"it over: {join_ids(enjoys)}. Wants to edit any plan rather than have an app "
        f'"dictating": {join_ids(control)} (a templated sentence). The only enthusiasm for '
        f"fully automatic planning comes from the led interview {join_ids(excluded)}.",
        tuple(sorted(set(resist) | set(enjoys) | set(control))),
        "So the agent will present the weekly-plan format as an open question, not a "
        "validated need, and propose comparing a weekly plan with same-day 'what can I cook "
        "tonight' suggestions.",
    ))

    cadence = {k: sorted(i for i, c in coding.items() if c.shopping_pattern == k)
               for k in ("weekly", "daily", "ad_hoc")}
    add(Finding(
        "F13", "Q3", "Only some households shop in a weekly rhythm",
        f"Weekly shoppers: {join_ids(cadence['weekly'])}. Near-daily: "
        f"{join_ids(cadence['daily'])}. Ad hoc, glancing in the fridge before leaving: "
        f"{join_ids(cadence['ad_hoc'])}.",
        tuple(sorted(i for ids in cadence.values() for i in ids)),
        "So the agent will flag that a weekly plan with a weekly shopping list fits weekly "
        "shoppers best, and will treat shopping rhythm as a way to segment users.",
    ))

    add(Finding(
        "F14", "Q3", "The 'stop arguing' promise is barely supported",
        f"The idea brief promises households will {IDEA_CLAIMS['stop_arguing']}. Only P02 "
        "describes an argument about what to eat, and P04 a nightly negotiation with "
        "children. Coordination problems are mostly about shopping (duplicates, shared "
        "lists), not dinner arguments.",
        ("P02", "P04", "P10"),
        "So the agent will mark the 'stop arguing' part of the value proposition as weakly "
        "supported and reframe it as a shopping-coordination problem where the evidence "
        "allows.",
    ))

    # Q4 - competitors and market snippets --------------------------------------------------
    stale = sorted(comp.index[comp["freshness"] == "stale"])
    no_url = sorted(comp.index[comp["source_url"].isna()])
    current = comp[comp["freshness"] == "current"]
    add(Finding(
        "F15", "Q4",
        f"Competitor rows: {len(stale)} stale, {len(no_url)} without a source",
        "; ".join(f"{name} was last verified {int(comp.loc[name, 'days_since_verified'])} "
                  f"days before the research date" for name in stale)
        + f". {join_ids(no_url)} has no source URL. The other {len(current)} rows were "
        f"verified within {int(current['days_since_verified'].max())} days. All URLs are "
        f"placeholder domains, so the CSV row is the citable source.",
        tuple(stale) + tuple(no_url),
        "So the agent will cite competitors by name with their last_verified date, caveat "
        f"{join_ids(stale)} as possibly outdated, and mark {join_ids(no_url)} details as "
        "unsourced.",
    ))

    combined = sorted(caps.index[(caps["knows_inventory"] == 1) & (caps["weekly_plan"] == 1)])
    coverage = "; ".join(
        f"{label.lower()}: {join_ids(sorted(caps.index[caps[key] == 1]))}"
        for key, (label, _) in CAPABILITIES.items()
    )
    add(Finding(
        "F16", "Q4", "The pitch already exists on the market, in pieces",
        f"Every part of the PantryPal pitch is offered by at least one competitor ({coverage}). "
        f"{'No' if not combined else join_ids(combined)} competitor combines knowing the "
        f'inventory with a weekly plan. The idea brief\'s claim "'
        f'{IDEA_CLAIMS["knows_what_you_own"]}" is contradicted by {join_ids(inventory)}.',
        tuple(caps.index),
        "So the agent will describe differentiation as the combination of inventory "
        "awareness and weekly planning, not either one alone, and will mark the idea-brief "
        "claim as contradicted by the competitor rows.",
        headline=True,
    ))

    paid = comp["lowest_paid_eur_month"].dropna()
    free = sorted(comp.index[comp["has_free_tier"]])
    add(Finding(
        "F17", "Q4", "Competitor prices anchor at a few euros a month",
        f"The lowest paid prices (annual plans converted to per month) run from "
        f"EUR {paid.min():.2f} to EUR {paid.max():.2f} across {len(paid)} competitors; "
        f"{join_ids(free)} offer a free tier. This matches "
        f'the S05 median of {s05.stat} and the "few euros" heard in interviews.',
        tuple(sorted(paid.index)) + tuple(free) + ("S05",),
        "So the agent will keep pricing hypotheses inside the band set by competitors and "
        "S05, and treat any higher price as untested.",
    ))

    by_rel = {r: sorted(snip.index[snip["reliability"] == r])
              for r in ("usable", "usable_with_caveat", "unsupported", "unreliable", "stale")}
    citable = sorted(by_rel["usable"] + by_rel["usable_with_caveat"])
    not_citable = by_rel["unsupported"] + by_rel["unreliable"] + by_rel["stale"]
    add(Finding(
        "F18", "Q4", f"Only {len(citable)} of {len(snip)} market snippets can back a claim",
        f"Usable: {join_ids(by_rel['usable'])}; usable with an age caveat: "
        f"{join_ids(by_rel['usable_with_caveat'])}. No source: "
        f"{join_ids(by_rel['unsupported'])}. Unreliable: {join_ids(by_rel['unreliable'])} "
        f"(a blog claiming 97% would pay, contradicting S03 and S05). Stale: "
        f"{join_ids(by_rel['stale'])} (from {snip.loc[by_rel['stale'][0], 'year']}). S03 "
        f"itself is a caution: only {p.dataset.snippets['S03'].stat} of households use a "
        f"meal-planning app.",
        tuple(snip.index),
        f"So the agent will cite only {join_ids(citable)} as market evidence (with the age "
        f"caveat on {join_ids(by_rel['usable_with_caveat'])}), mark any claim "
        f"that rests on {join_ids(not_citable)} as unsupported, and never repeat those "
        "figures as fact.",
        headline=True,
    ))

    # Q5 - gaps ---------------------------------------------------------------------------
    add(Finding(
        "F19", "Q5", "What the data cannot answer",
        "Missing: country, income and recruitment of participants; behaviour over time "
        "(usage, measured waste; waste figures are self-estimates); how people would want to "
        "tell the app what they own (photo, barcode, receipt, online order history); whether "
        "anyone keeps planning after week one; competitor traction (users, ratings, churn); "
        "market size for the target segment specifically; and who in the household decides "
        "and who pays.",
        (),
        "So the agent will list these as open questions under 'what to test next' and will "
        "not fill them with assumptions or outside knowledge.",
        headline=True,
    ))
    return findings
