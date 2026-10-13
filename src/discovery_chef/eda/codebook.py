"""Explicit codebooks used by the EDA.

Themes are coded with transparent patterns applied to participant answers only (never to
interviewer questions), so anyone can rerun the coding and audit every match. The patterns
were written after reading these transcripts: this is an analyst's codebook, not automatic
theme discovery. Phase 3 compares these themes with the ones the agents and clustering find.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Kinds of interview theme:
#   problem          - a pain the product idea claims to solve
#   requirement      - a condition participants put on any solution
#   counter_evidence - a statement that cuts against the idea
THEME_KINDS = ("problem", "requirement", "counter_evidence")


@dataclass(frozen=True)
class Theme:
    key: str
    label: str
    kind: str
    pattern: re.Pattern[str]

    def matches(self, sentence: str) -> bool:
        return bool(self.pattern.search(sentence))


def _theme(key: str, label: str, kind: str, *patterns: str) -> Theme:
    assert kind in THEME_KINDS, kind
    return Theme(key, label, kind, re.compile("|".join(patterns), re.IGNORECASE))


THEMES: tuple[Theme, ...] = (
    _theme(
        "food_waste", "Food goes off and is thrown away", "problem",
        r"\bthrow (away|out)\b", r"\bthrew out\b", r"\bbin them\b", r"\bwent (bad|slimy)\b",
        r"\bgoes bad\b", r"\bgo off\b", r"\balready off\b", r"\bwaste\b",
    ),
    _theme(
        "forgotten_inventory", "Loses track of what is already at home", "problem",
        r"\bforget half\b", r"\bforgot about the fridge\b", r"\bforget small things\b",
        r"\bdisappear in the back\b", r"\bremembers what we already have\b",
        r"\bthought we were out\b",
    ),
    _theme(
        "duplicate_purchases", "Buys duplicates or the wrong items", "problem",
        r"\btwo packs of the same\b", r"\bbought \w+ twice\b", r"\bbuy duplicates\b",
        r"\bI bought chicken\b", r"\bnothing for the planned recipe\b",
    ),
    _theme(
        "uncoordinated_household", "Household members do not coordinate food decisions",
        "problem",
        r"\bnot in a coordinated way\b", r"\bbuys without checking\b", r"\bgroup chat\b",
        r"\bnobody replaces it\b", r"\bexactly the problem\b", r"\bboth shop\b",
    ),
    _theme(
        "decision_fatigue", "Deciding what to cook every day is a burden", "problem",
        r"\bmental load\b", r"\bdecide what's for dinner\b", r"\bdaily question\b",
        r"\bno ideas left\b", r"\bdread\b", r"\bdeciding is exhausting\b",
        r"\bargued for ten minutes\b",
    ),
    _theme(
        "time_pressure", "Little time or energy on weeknights", "problem",
        r"\bchaos\b", r"\bget home late\b", r"\bsomething quick\b", r"\bhome at eight\b",
    ),
    _theme(
        "grocery_cost", "Grocery and takeaway costs hurt", "problem",
        r"\bcheaper\b", r"\boverspend\b", r"\bafford\b", r"\beuros a week\b",
        r"\bcost me\b", r"\beuros of food\b",
    ),
    _theme(
        "household_preferences", "Picky eaters, allergies and preferences", "requirement",
        r"\ballergies\b", r"\bwhat we actually like\b", r"\bfood they refuse\b",
        r"\bhates peppers\b",
    ),
    _theme(
        "fast_setup", "Setup must be fast; will not type in the whole pantry", "requirement",
        r"\bsetup has to be fast\b", r"\btype in my whole pantry\b",
    ),
    _theme(
        "user_control", "Wants to edit the plan; no app dictating", "requirement",
        r"\bedit the plan\b", r"\bdictating\b",
    ),
    _theme(
        "quick_recipes", "Recipes must be realistic for weeknights (30 min)", "requirement",
        r"\brealistic for weeknights\b", r"\bthirty minutes at most\b",
    ),
    _theme(
        "low_effort", "Must not feel like a project or homework", "requirement",
        r"\bwithout being a project\b", r"\bfeel like homework\b", r"\btook no effort\b",
    ),
    _theme(
        "flexibility", "Must flex to how each household works", "requirement",
        r"\bhas to flex\b",
    ),
    _theme(
        "privacy", "Distrusts apps with shopping data", "requirement",
        r"\bdon't trust apps\b", r"\bprivate\b",
    ),
    # Only explicit rejection of planning. Improvising ("wing it", "improvise") is a habit,
    # not a verdict on planning, so it is not counted here.
    _theme(
        "planning_resistance", "Rejects planning ahead, or gave up on a planning app",
        "counter_evidence",
        r"\bplanning ahead stresses me out\b", r"\bplan I don't follow\b",
        r"\bstopped opening it\b", r"\bdecide on the day\b",
    ),
    _theme(
        "enjoys_planning", "Enjoys planning and wants to keep doing it", "counter_evidence",
        r"\bplanning is my favourite\b", r"\btake that away\b",
    ),
    _theme(
        "no_pain", "Reports little or no problem with dinner today", "counter_evidence",
        r"\bnot much, honestly\b", r"\bisn't a problem\b", r"\benough for it to bother me\b",
        r"\bnever needed one\b",
    ),
    _theme(
        "would_not_pay", "Would not pay for it", "counter_evidence",
        r"\bwouldn't pay\b", r"\bcan't imagine paying\b",
    ),
)

THEMES_BY_KEY = {theme.key: theme for theme in THEMES}


# Leading-question patterns. A leading question suggests its own answer, so the reply
# tells us about the interviewer more than the participant.
LEADING_PATTERNS: dict[str, re.Pattern[str]] = {
    "negative_interrogative": re.compile(
        r"^(don't|doesn't|wouldn't|isn't|aren't|won't|can't|didn't)\b", re.IGNORECASE
    ),
    "tag_question": re.compile(
        r",\s*(isn't|wasn't|doesn't|don't|wouldn't|won't|aren't|is|right)"
        r"(\s+(it|there|you|they|that))?\?\s*$",
        re.IGNORECASE,
    ),
    "presumption": re.compile(r"\b(I imagine|I bet|must be|must have|surely)\b", re.IGNORECASE),
    "loaded_wording": re.compile(r"\b(nightmare|amazing|struggle|definitely)\b", re.IGNORECASE),
}

# Milder: neutral-sounding guide questions that still presuppose a problem exists.
PRESUPPOSING_PATTERN = re.compile(r"\bmost frustrating\b|\bwent wrong\b", re.IGNORECASE)

# Answers that agree without adding content (typical reply to a leading question).
ACQUIESCENT_PATTERN = re.compile(r"^(yes|yeah|sure|probably|i guess)\b", re.IGNORECASE)


# Instruction-like text inside data files (prompt injection). Data is never instructions;
# this scan only tells us whether the dataset tries.
INJECTION_PATTERN = re.compile(
    r"ignore (all |any )?(previous|prior|above)|disregard (the|all|previous)|system prompt"
    r"|you are an? (ai|assistant|language model)|\bas an ai\b|new instructions"
    r"|follow these instructions|<\s*/?\s*(system|assistant|instructions?)\s*>",
    re.IGNORECASE,
)


# What PantryPal promises (from idea_brief.md), coded against competitor positioning and
# key_features so we can see which parts of the pitch are already on the market.
CAPABILITIES: dict[str, tuple[str, re.Pattern[str]]] = {
    "knows_inventory": (
        "Knows what you already own",
        re.compile(r"photos? of your fridge|photo recognition|pantry inventory|barcode",
                   re.IGNORECASE),
    ),
    "weekly_plan": (
        "Weekly dinner plan",
        re.compile(r"weekly (meal )?plan|weekly plans|meal planning calendar|dinner planner"
                   r"|meal plans|\bplans\b", re.IGNORECASE),
    ),
    "shopping_list": (
        "Shopping list",
        re.compile(r"grocery list|shopping list|shared list", re.IGNORECASE),
    ),
    "household_sharing": (
        "Shared across the household",
        re.compile(r"family sharing|shared plans|shared household|shared list", re.IGNORECASE),
    ),
    "waste_reduction": (
        "Reduces food waste",
        re.compile(r"expiry|leftover|use-it-up|reduce waste", re.IGNORECASE),
    ),
}
