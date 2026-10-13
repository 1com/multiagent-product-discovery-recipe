"""Hand-off contracts: what each agent must return, enforced by structured outputs.

Citation IDs everywhere: interview turns "P02:t4", whole interviews "P02", competitor rows
"C:MealLoop", market snippets "S05".
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

SourceId = str


class Evidence(BaseModel):
    source_id: SourceId = Field(description="Citation ID, e.g. 'P02:t4', 'C:MealLoop' or 'S05'.")
    quote: str = Field(description="Words copied exactly from that source. Never paraphrase "
                       "inside this field.")
    kind: Literal["behaviour", "stated_preference", "document_fact"] = Field(
        description="behaviour = something the participant did; stated_preference = an "
        "opinion, wish or prediction; document_fact = a competitor row or market snippet.")


# --- Research synthesiser ------------------------------------------------------------------

class Segment(BaseModel):
    name: str
    interview_ids: list[str]
    target_fit: Literal["in", "partial", "out", "mixed"]
    description: str
    needs: list[str]


class Insight(BaseModel):
    id: str = Field(description="R1, R2, ...")
    kind: Literal["problem", "requirement", "counter_evidence", "behaviour_pattern"]
    statement: str
    interview_ids: list[str] = Field(description="Distinct interviews that support it.")
    own_words_interviews: list[str] = Field(
        description="Subset whose support is not only a templated sentence.")
    evidence: list[Evidence]
    strength: Literal["strong", "moderate", "weak"]
    caveats: list[str]


class Position(BaseModel):
    stance: str
    interview_ids: list[str]
    evidence: list[Evidence]


class Disagreement(BaseModel):
    topic: str
    positions: list[Position]
    implication: str


class ResearchSynthesis(BaseModel):
    segments: list[Segment]
    insights: list[Insight]
    disagreements: list[Disagreement]
    willingness_to_pay: str
    willingness_to_pay_evidence: list[Evidence]
    evidence_set_aside: list[str] = Field(
        description="Evidence you excluded or down-weighted, and why.")


# --- Competitor and market analyst ---------------------------------------------------------

Capability = Literal["knows_inventory", "weekly_plan", "shopping_list", "household_sharing",
                     "waste_reduction", "budget_focus"]


class CompetitorAssessment(BaseModel):
    competitor: str = Field(description="Exact name from competitors.csv.")
    overlap_with_pantrypal: list[Capability]
    pricing_summary: str
    data_quality: Literal["current", "stale", "unsourced"]
    threat: Literal["high", "medium", "low"]
    rationale: str


class MarketFigure(BaseModel):
    snippet_id: str
    figure: str
    usable_as_evidence: bool
    how_to_use: str


class ClaimCheck(BaseModel):
    claim: str = Field(description="The idea-brief claim, quoted.")
    verdict: Literal["supported", "partly_supported", "unsupported", "contradicted"]
    source_ids: list[SourceId]
    explanation: str


class MarketAnalysis(BaseModel):
    competitors: list[CompetitorAssessment]
    white_space: list[str] = Field(description="Openings no competitor covers, with "
                                   "citation IDs inline.")
    pricing_anchors: str
    market_figures: list[MarketFigure]
    idea_claim_checks: list[ClaimCheck]


# --- Risk and assumption analyst -----------------------------------------------------------

class Assumption(BaseModel):
    id: str = Field(description="A1, A2, ...")
    statement: str
    category: Literal["desirability", "viability", "feasibility", "usability"]
    evidence_for: list[SourceId]
    evidence_against: list[SourceId]
    confidence: Literal["low", "medium", "high"] = Field(
        description="How sure the evidence lets us be that the assumption holds.")
    impact_if_wrong: Literal["low", "medium", "high"]
    rationale: str


class Experiment(BaseModel):
    id: str = Field(description="E1, E2, ...")
    tests_assumptions: list[str]
    hypothesis: str
    method: str
    success_metric: str
    cost: Literal["low", "medium", "high"]


class RiskAnalysis(BaseModel):
    assumptions: list[Assumption]
    riskiest_assumptions: list[str] = Field(description="Assumption IDs, riskiest first.")
    experiments: list[Experiment]
    open_questions: list[str]
    suggested_recommendation: Literal["build", "pivot", "test_further"]
    recommendation_reason: str


# --- Brief writer --------------------------------------------------------------------------

BRIEF_SECTIONS = (
    "## 1. Recommendation",
    "## 2. Who the users are",
    "## 3. Problems that are real",
    "## 4. What the evidence says",
    "## 5. Competitors and market",
    "## 6. Risks and open assumptions",
    "## 7. What to test next",
    "## 8. Unsupported or weak claims",
)


class DiscoveryBrief(BaseModel):
    recommendation: Literal["build", "pivot", "test_further"]
    one_line_rationale: str
    markdown: str = Field(description="The full brief in Markdown, starting with "
                          "'# PantryPal discovery brief' and using the required sections.")

    @field_validator("markdown")
    @classmethod
    def _real_line_breaks(cls, text: str) -> str:
        """Models sometimes double-escape newlines inside the JSON string, which leaves
        literal backslash-n in the text. Decode them when they outnumber real ones."""
        if text.count("\\n") > text.count("\n"):
            text = text.replace("\\n", "\n").replace('\\"', '"')
        return text


# --- Critic --------------------------------------------------------------------------------

class Objection(BaseModel):
    id: str = Field(description="O1, O2, ... numbered within this review.")
    severity: Literal["blocker", "major", "minor"]
    category: Literal["unsupported_claim", "wrong_citation", "misquote", "invented_number",
                      "excluded_source", "overclaim", "missing_content", "contradiction",
                      "unclear"]
    section: str
    excerpt: str = Field(description="The brief text at issue, copied exactly.")
    problem: str
    fix: str


class Critique(BaseModel):
    verdict: Literal["approve", "revise"]
    summary: str
    objections: list[Objection]
    resolved_from_previous: list[str] = Field(
        description="Earlier objections (by excerpt or ID) that this draft now fixes.")
