"""Analyst coding of the research data: the judgement calls the EDA rests on.

Everything here is interpretation, not data. Each judgement carries the verbatim quotes it
rests on; `tests/test_annotations.py` fails if any quote is not found word for word in its
source file, so the coding cannot drift from the transcripts.

Target customer (idea_brief.md): "households of two or more people who cook at home on
most weeknights". Fit is coded on both criteria:
    in      - both criteria met
    partial - two or more people, but cooking at home is irregular or not shared
    out     - neither criterion met
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Issue:
    """A data-quality problem inside one interview.

    `scope` is "interview" when the problem undermines the whole transcript (it lowers the
    interview's evidence weight) or a topic name ("wtp", "shopping") when only claims on
    that topic need a caveat.
    """

    kind: str
    severity: str  # "major" | "minor"
    scope: str
    note: str
    quotes: tuple[str, ...]


@dataclass(frozen=True)
class WillingnessToPay:
    category: str  # see WTP_CATEGORIES
    max_eur_per_month: float | None
    quote: str


WTP_CATEGORIES = {
    "none": "Would not pay",
    "free_or_conditional": "Free with ads, or pays only if waste visibly drops",
    "low_conditional": "A few euros, only if it clearly saves money",
    "low": "Up to about EUR 6/month",
    "high_outlier": "Far above the market median; anchored on a one-off event",
    "unusable": "Answer to a leading question",
}


HOUSEHOLD_TYPES = {
    "family_with_children": "Family with children",
    "couple_no_children": "Couple without children",
    "flatmates": "Flatmates sharing a kitchen",
    "single": "Lives alone",
}


@dataclass(frozen=True)
class InterviewCoding:
    interview_id: str
    household_type: str  # see HOUSEHOLD_TYPES
    household_size: int  # minimum size stated or implied by persona and transcript
    cooks_most_weeknights: str  # "yes" | "partly" | "no" | "unclear"
    target_fit: str  # "in" | "partial" | "out"
    fit_rationale: str
    fit_quotes: tuple[str, ...]
    shopping_pattern: str  # "weekly" | "daily" | "ad_hoc" | "unknown"
    shopping_quote: str | None
    current_tools: str
    tools_quote: str | None
    wtp: WillingnessToPay
    issues: tuple[Issue, ...] = field(default_factory=tuple)


INTERVIEW_CODING: dict[str, InterviewCoding] = {
    c.interview_id: c
    for c in (
        InterviewCoding(
            interview_id="P01",
            household_type="family_with_children",
            household_size=4,
            cooks_most_weeknights="yes",
            target_fit="in",
            fit_rationale="Family of four with two working parents; dinner is cooked at "
            "home every weeknight under time pressure.",
            fit_quotes=(
                "Mother of two (6 and 9), both parents work full-time",
                "Dinner is whatever I can get on the table in thirty minutes.",
            ),
            shopping_pattern="weekly",
            shopping_quote="I order online every week, mostly the same basket.",
            current_tools="Notes app for the list; screenshotted recipes",
            tools_quote="A notes app for the list, and I screenshot recipes that I never cook.",
            wtp=WillingnessToPay(
                "low_conditional", None,
                "A few euros a month, maybe, if it clearly saves me money on groceries.",
            ),
        ),
        InterviewCoding(
            interview_id="P02",
            household_type="couple_no_children",
            household_size=2,
            cooks_most_weeknights="yes",
            target_fit="in",
            fit_rationale="Couple who mostly cook something quick at home on weeknights, "
            "with occasional takeaway.",
            fit_quotes=(
                "Couple in their thirties, no children",
                "We both get home late, so it's usually pasta or something quick.",
            ),
            shopping_pattern="ad_hoc",
            shopping_quote="I glance in the fridge before I leave, but only roughly.",
            current_tools="Shared list app",
            tools_quote="We use a shared list app, but it's only a list.",
            wtp=WillingnessToPay(
                "low", 6.0,
                "Maybe five or six euros. More than that and I'd just keep my notes app.",
            ),
            issues=(
                Issue(
                    kind="internal_inconsistency",
                    severity="minor",
                    scope="interview",
                    note="Says they use a shared list app, then compares the price against "
                    "'my notes app'.",
                    quotes=(
                        "We use a shared list app, but it's only a list.",
                        "More than that and I'd just keep my notes app.",
                    ),
                ),
            ),
        ),
        InterviewCoding(
            interview_id="P03",
            household_type="family_with_children",
            household_size=2,
            cooks_most_weeknights="yes",
            target_fit="in",
            fit_rationale="Single parent and child; cooks every night for budget reasons.",
            fit_quotes=(
                "Single parent of one child",
                "I cook every night because it's cheaper.",
            ),
            shopping_pattern="weekly",
            shopping_quote="I shop once a week, usually on Saturday, plus a couple of "
            "top-up trips.",
            current_tools="Paper pad on the fridge",
            tools_quote="A paper pad on the fridge.",
            wtp=WillingnessToPay(
                "free_or_conditional", None,
                "Only if it clearly reduced food waste. A free version with ads would also "
                "be fine.",
            ),
            issues=(
                Issue(
                    kind="internal_contradiction",
                    severity="major",
                    scope="interview",
                    note="Calls planning the favourite part of the week, then calls deciding "
                    "exhausting. The planning burden is the core problem PantryPal targets, "
                    "so neither statement can stand alone.",
                    quotes=(
                        "Planning is my favourite part of the week, honestly.",
                        "Deciding is exhausting.",
                    ),
                ),
            ),
        ),
        InterviewCoding(
            interview_id="P04",
            household_type="family_with_children",
            household_size=5,
            cooks_most_weeknights="yes",
            target_fit="in",
            fit_rationale="Family of five; dinner is cooked and negotiated every night.",
            fit_quotes=(
                "Father of three (4, 7, 11), partner works shifts",
                "Dinner is a negotiation every night.",
            ),
            shopping_pattern="weekly",
            shopping_quote="I shop once a week, usually on Saturday, plus a couple of "
            "top-up trips.",
            current_tools="Shared list app",
            tools_quote="We use a shared list app, but it's only a list.",
            wtp=WillingnessToPay(
                "low_conditional", None,
                "A few euros a month, maybe, if it clearly saves me money on groceries.",
            ),
            issues=(
                Issue(
                    kind="attribution_inconsistency",
                    severity="major",
                    scope="interview",
                    note="The persona is a father who talks about 'my wife', then lists "
                    "'my husband'. It is unclear who is speaking, so the transcript may mix "
                    "two people or be mislabelled.",
                    quotes=(
                        "Father of three",
                        "my wife buys without checking",
                        "Me, my husband and, loudly, three children.",
                    ),
                ),
            ),
        ),
        InterviewCoding(
            interview_id="P05",
            household_type="couple_no_children",
            household_size=2,
            cooks_most_weeknights="partly",
            target_fit="partial",
            fit_rationale="Two people eating at home, but with no routine: food is decided "
            "on the day and is sometimes not cooked at all.",
            fit_quotes=(
                "Freelance couple working from home",
                "There is no routine, I just get hungry and figure it out.",
                "We had toast with whatever cheese was left.",
            ),
            shopping_pattern="daily",
            shopping_quote="I go to the shop almost every day and buy as I go.",
            current_tools="Nothing; occasional delivery app",
            tools_quote="Nothing really, maybe a delivery app now and then.",
            wtp=WillingnessToPay(
                "none", 0.0, "Honestly I wouldn't pay for it. I'd want a free version."
            ),
        ),
        InterviewCoding(
            interview_id="P06",
            household_type="family_with_children",
            household_size=3,
            cooks_most_weeknights="unclear",
            target_fit="in",
            fit_rationale="Working parent of two, so on paper inside the target. Nothing "
            "in the transcript can be relied on (see issues).",
            fit_quotes=("Mother of two, works full-time",),
            shopping_pattern="unknown",
            shopping_quote=None,
            current_tools="Unknown (question was leading)",
            tools_quote=None,
            wtp=WillingnessToPay("unusable", None, "Probably, yes. Hmm, yes. Why not."),
            issues=(
                Issue(
                    kind="leading_interview",
                    severity="major",
                    scope="interview",
                    note="Almost every question suggests its own answer, and the replies "
                    "simply agree. The opening answer is also a word-for-word copy of P01.",
                    quotes=(
                        "Wouldn't it be amazing if an app just planned all your meals "
                        "automatically?",
                        "Yes, definitely, if it did all that.",
                        "Surely there's no good tool for this today, is there?",
                        "Sure, that sounds good.",
                    ),
                ),
            ),
        ),
        InterviewCoding(
            interview_id="P07",
            household_type="single",
            household_size=1,
            cooks_most_weeknights="no",
            target_fit="out",
            fit_rationale="Student living alone who cooks about once a week; fails both "
            "target criteria.",
            fit_quotes=(
                "University student living alone",
                "I cook maybe once a week when I have time.",
            ),
            shopping_pattern="ad_hoc",
            shopping_quote="I buy pasta, eggs and whatever is on offer, nothing planned.",
            current_tools="Nothing; occasional delivery app",
            tools_quote="Nothing really, maybe a delivery app now and then.",
            wtp=WillingnessToPay(
                "none", 0.0,
                "If it were free and took no effort maybe, but I can't imagine paying for it.",
            ),
        ),
        InterviewCoding(
            interview_id="P08",
            household_type="couple_no_children",
            household_size=2,
            cooks_most_weeknights="partly",
            target_fit="partial",
            fit_rationale="Two-person household, but both travel for work and improvise "
            "when home.",
            fit_quotes=(
                "Couple in their forties, both travel for work",
                "Last Tuesday I was away for work and my partner ate crackers.",
                "When I'm home we usually wing it.",
            ),
            shopping_pattern="ad_hoc",
            shopping_quote="I glance in the fridge before I leave, but only roughly.",
            current_tools="Follows recipe accounts; rarely cooks from them",
            tools_quote="I follow a few recipe accounts for ideas and almost never cook "
            "from them.",
            wtp=WillingnessToPay(
                "high_outlier", 30.0,
                "For something that would stop that, I'd pay thirty euros a month, easy.",
            ),
            issues=(
                Issue(
                    kind="outlier_claim",
                    severity="major",
                    scope="wtp",
                    note="EUR 30/month is anchored on one holiday incident, not on weekly "
                    "dinner planning, and a dinner planner would not obviously have "
                    "prevented it. Keep the fridge-waste story, drop the price from any "
                    "average.",
                    quotes=(
                        "Last summer we went on holiday for three weeks and I forgot about "
                        "the fridge.",
                        "For something that would stop that, I'd pay thirty euros a month, "
                        "easy.",
                    ),
                ),
            ),
        ),
        InterviewCoding(
            interview_id="P09",
            household_type="couple_no_children",
            household_size=2,
            cooks_most_weeknights="yes",
            target_fit="in",
            fit_rationale="Retired couple who cook every day: inside the target, but with "
            "no reported pain. Being in the target is not the same as having the problem.",
            fit_quotes=(
                "Retired couple in their seventies, cook every day",
                "We cook every day, we've done it for forty years.",
            ),
            shopping_pattern="daily",
            shopping_quote="I go to the shop almost every day and buy as I go.",
            current_tools="Paper pad on the fridge",
            tools_quote="A paper pad on the fridge.",
            wtp=WillingnessToPay(
                "none", 0.0, "Honestly I wouldn't pay for it. I'd want a free version."
            ),
            issues=(
                Issue(
                    kind="internal_inconsistency",
                    severity="minor",
                    scope="interview",
                    note="Weekly shopping at one stall versus shopping almost daily; a "
                    "decades-old fixed routine versus 'not in a coordinated way'.",
                    quotes=(
                        "We shop at the same stall every week.",
                        "I go to the shop almost every day and buy as I go.",
                        "That has not changed in decades.",
                        "Both of us, but not in a coordinated way.",
                    ),
                ),
            ),
        ),
        InterviewCoding(
            interview_id="P10",
            household_type="flatmates",
            household_size=4,
            cooks_most_weeknights="partly",
            target_fit="partial",
            fit_rationale="Four flatmates share a kitchen and staples, but mostly cook "
            "for themselves; the pain is shared inventory rather than a shared dinner.",
            fit_quotes=(
                "Four flatmates (late twenties) sharing one kitchen",
                "Four of us share the kitchen, so mostly everyone cooks for themselves.",
            ),
            shopping_pattern="ad_hoc",
            shopping_quote="I glance in the fridge before I leave, but only roughly.",
            current_tools="Shared list app and a group chat",
            tools_quote="We use a shared list app, but it's only a list.",
            wtp=WillingnessToPay(
                "low_conditional", None,
                "A few euros a month, maybe, if it clearly saves me money on groceries.",
            ),
        ),
    )
}


# Evidence weight = quality x fit. These numbers are analyst choices, published so they
# can be challenged. They only rank and weight evidence; they never hide it.
QUALITY_PENALTY = {"major": 0.3, "minor": 0.1}
FIT_FACTOR = {"in": 1.0, "partial": 0.5, "out": 0.25}
# An interview whose questions are mostly leading carries no usable evidence.
LEADING_EXCLUSION_THRESHOLD = 0.5
EVIDENCE_TIERS = (  # (minimum weight, tier), checked top-down
    (0.8, "primary"),
    (0.4, "supporting"),
    (0.01, "contrast_only"),
    (0.0, "excluded"),
)


@dataclass(frozen=True)
class SnippetCheck:
    """A cross-check on a market snippet that the automated checks cannot see."""

    kind: str
    note: str
    conflicts_with: tuple[str, ...] = ()


SNIPPET_CHECKS: dict[str, SnippetCheck] = {
    "S06": SnippetCheck(
        kind="scope_conflation",
        note="Bundles meal-planning apps with meal kits; meal-kit growth says nothing about "
        "demand for a planning app.",
    ),
    "S08": SnippetCheck(
        kind="implausible",
        note="97% would pay contradicts the 11% who use a planning app (S03), the "
        "EUR 3.50 median willingness to pay (S05) and three of ten interviewees who would "
        "not pay at all.",
        conflicts_with=("S03", "S05", "P05", "P07", "P09"),
    ),
}

# Idea-brief claims checked against the data. Each is a sentence from idea_brief.md.
IDEA_CLAIMS: dict[str, str] = {
    "knows_what_you_own": "Existing recipe apps give ideas but do not know what you "
    "already own.",
    "stop_arguing": 'stop arguing about "what\'s for dinner"',
}
