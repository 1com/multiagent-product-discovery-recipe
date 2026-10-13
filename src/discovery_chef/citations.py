"""Deterministic checks on a brief's citations, quotes and numbers.

Cheap, exact and model-free, so the critic can spend its effort on whether a source
*supports* a claim rather than on whether the source exists. The same report scores the
multi-agent brief and the single-prompt baseline in the evaluation.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from discovery_chef.agents.contracts import BRIEF_SECTIONS
from discovery_chef.context import INTERVIEW_TURN, DiscoveryContext

_BRACKET = re.compile(r"\[([^\[\]]+)\](?!\()")  # skip Markdown links [text](url)
# Anything shaped like a citation ID, valid or not: P02:t4, S05, C:MealLoop, idea_brief,
# UNSUPPORTED, but also internal IDs an agent might wrongly cite (F16, A1, R2, E1).
_ID = re.compile(r"^([A-Z]{1,2}\d{1,3}(:t\d{1,2})?|C:.+|idea_brief|UNSUPPORTED)$")
_QUOTE = re.compile(r"[\"“]([^\"“”]{3,}?)[\"”]")
_NUMBER = re.compile(
    r"(?:EUR|€)\s?(\d+(?:[.,]\d+)?)"  # EUR 3.50, €118
    r"|(\d+(?:\.\d+)?)\s?(?:%|percent\b)"  # 19%, 70 percent
    r"|(\d+(?:\.\d+)?)\s?(?:euros?|minutes|days|years|hours)\b",  # 22 minutes
    re.IGNORECASE,
)
_DATE = re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b")
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60,
}
# Words showing a line discusses a source as flawed rather than relying on it (F04 allows
# citing P06 "only as a research-method problem").
_HEDGE_WORDS = re.compile(r"unsupported|unreliable|stale|no source|not (be )?(used|cited)|"
                          r"blog|discard|ignore|cannot|can't|weak|outdated|caution|"
                          r"exclud|zero (evidence )?weight|leading|methodolog|research.method",
                          re.IGNORECASE)
MIN_QUOTE_WORDS = 4
MIN_CLAIM_WORDS = 12


@dataclass
class CitationReport:
    citations: int = 0
    distinct_sources: int = 0
    unknown_ids: list[str] = field(default_factory=list)
    excluded_citations: list[str] = field(default_factory=list)
    weak_snippet_citations: list[str] = field(default_factory=list)
    misquotes: list[str] = field(default_factory=list)
    verified_quotes: int = 0
    unverified_numbers: list[str] = field(default_factory=list)
    wrong_dates: list[str] = field(default_factory=list)
    uncited_claims: list[str] = field(default_factory=list)
    claim_lines: int = 0
    unsupported_flags: int = 0
    missing_sections: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        if not self.claim_lines:
            return 0.0
        return round(1 - len(self.uncited_claims) / self.claim_lines, 3)

    @property
    def blocking(self) -> int:
        return (len(self.unknown_ids) + len(self.excluded_citations) + len(self.misquotes)
                + len(self.wrong_dates) + len(self.missing_sections))

    @property
    def passed(self) -> bool:
        return self.blocking == 0

    def to_dict(self) -> dict:
        return {**asdict(self), "coverage": self.coverage, "blocking": self.blocking,
                "passed": self.passed}

    def render(self) -> str:
        lines = [
            f"Automated citation check: {'PASSED' if self.passed else 'FAILED'} "
            f"({self.blocking} blocking issues)",
            f"- {self.citations} citations to {self.distinct_sources} distinct sources; "
            f"{self.coverage:.0%} of {self.claim_lines} claim lines carry a citation "
            f"or [UNSUPPORTED].",
            f"- Quotes verified word for word: {self.verified_quotes}.",
        ]
        checks = [
            ("Unknown citation IDs", self.unknown_ids),
            ("Citations to excluded interviews", self.excluded_citations),
            ("Quotes not found word for word in the cited source", self.misquotes),
            ("Dates not found in the data", self.wrong_dates),
            ("Missing required sections", self.missing_sections),
            ("Unusable market snippets cited without a caveat", self.weak_snippet_citations),
            ("Numbers not found in any source", self.unverified_numbers),
            ("Claim lines without a citation", self.uncited_claims),
        ]
        for title, items in checks:
            if items:
                lines.append(f"- {title}:")
                lines += [f"  - {item}" for item in items[:15]]
                if len(items) > 15:
                    lines.append(f"  - ... and {len(items) - 15} more")
        return "\n".join(lines)


def normalise(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return " ".join(text.lower().split())


def citation_ids(line: str) -> list[str]:
    ids = []
    for group in _BRACKET.findall(line):
        for token in re.split(r"[,;]", group):
            token = token.strip()
            if _ID.match(token):
                ids.append(token)
    return ids


def _number_words_to_digits(text: str) -> str:
    def hundreds(match):
        return str(_NUMBER_WORDS[match.group(1).lower()] * 100)

    text = re.sub(r"\b(" + "|".join(_NUMBER_WORDS) + r")\s+hundred\b", hundreds, text,
                  flags=re.IGNORECASE)
    return re.sub(r"\b(" + "|".join(_NUMBER_WORDS) + r")\b",
                  lambda m: str(_NUMBER_WORDS[m.group(1).lower()]), text, flags=re.IGNORECASE)


def _numbers_in(text: str) -> set[float]:
    return {float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?",
                                                          _number_words_to_digits(text))}


def known_numbers(ctx: DiscoveryContext) -> set[float]:
    """Every number in the data, the EDA findings, or the EDA's computed source fields."""
    texts = [ctx.dataset.idea.text]
    texts += [f["finding"] for f in ctx.profile["findings"]]
    texts += [f"{c['days_since_verified']} {c['lowest_paid_eur_month']}"
              for c in ctx.profile["competitors"].values()]
    texts += [str(s["age_years"]) for s in ctx.profile["market_snippets"].values()]
    texts += [i.text for i in ctx.dataset.interviews.values()]
    texts += [f"{c.pricing} {c.last_verified}" for c in ctx.dataset.competitors.values()]
    texts += [f"{s.stat} {s.year}" for s in ctx.dataset.snippets.values()]
    numbers: set[float] = set()
    for text in texts:
        numbers |= _numbers_in(text)
    return numbers


def known_dates(ctx: DiscoveryContext) -> set[str]:
    """Every date in the data: interview dates, competitor verification dates, as-of date."""
    dates = {i.date.isoformat() for i in ctx.dataset.interviews.values()}
    dates |= {c.last_verified.isoformat() for c in ctx.dataset.competitors.values()
              if c.last_verified}
    return dates | {ctx.profile["as_of"]}


def check_brief(markdown: str, ctx: DiscoveryContext) -> CitationReport:
    report = CitationReport()
    known = ctx.known_ids()
    excluded = set(ctx.excluded_interviews())
    citable = set(ctx.citable_snippets())
    numbers = known_numbers(ctx)
    dates = known_dates(ctx)
    interview_corpus = normalise("\n".join(
        [i.text for i in ctx.dataset.interviews.values()] + [ctx.dataset.idea.text]))
    all_ids: list[str] = []

    lines = markdown.splitlines()
    stripped = [line.strip() for line in lines]
    for section in BRIEF_SECTIONS:
        if not any(line.lower().startswith(section.lower()) for line in stripped):
            report.missing_sections.append(section)

    current_section = ""
    for line in stripped:
        if line.startswith("#"):
            current_section = line
            continue
        if not line or set(line) <= set("|-: "):
            continue
        ids = citation_ids(line)
        real_ids = [i for i in ids if i != "UNSUPPORTED"]
        all_ids += real_ids
        report.unsupported_flags += ids.count("UNSUPPORTED")

        for source_id in real_ids:
            if source_id not in known:
                report.unknown_ids.append(source_id)
                continue
            interview = INTERVIEW_TURN.match(source_id)
            interview_id = interview.group(1) if interview else source_id
            if interview_id in excluded and not _HEDGE_WORDS.search(line):
                report.excluded_citations.append(f"{source_id}: {line[:100]}")
            if source_id.startswith("S") and source_id not in citable \
                    and not _HEDGE_WORDS.search(line):
                report.weak_snippet_citations.append(f"{source_id}: {line[:100]}")

        for quote in _QUOTE.findall(line):
            if len(quote.split()) < MIN_QUOTE_WORDS:
                continue
            haystack = normalise("\n".join(ctx.raw_text(i) for i in real_ids if i in known))
            parts = [p.strip(" .,;:!?") for p in re.split(r"\.\.\.|…", normalise(quote))]
            parts = [p for p in parts if p]
            if all(p in haystack for p in parts) or (
                    not real_ids and all(p in interview_corpus for p in parts)):
                report.verified_quotes += 1
            else:
                report.misquotes.append(f'"{quote}" cited as {", ".join(real_ids) or "none"}')

        # Lines marked [UNSUPPORTED] may hold proposals ("test with 20 households").
        for match in ([] if "UNSUPPORTED" in ids else _NUMBER.finditer(line)):
            value = float(next(g for g in match.groups() if g).replace(",", "."))
            if value not in numbers:
                report.unverified_numbers.append(f"{match.group(0)}: {line[:100]}")

        for date in _DATE.findall(line):
            if date not in dates:
                report.wrong_dates.append(f"{date}: {line[:100]}")

        in_claim_section = any(current_section.lower().startswith(s.lower())
                               for s in BRIEF_SECTIONS[1:7])
        if in_claim_section and len(line.split()) >= MIN_CLAIM_WORDS:
            report.claim_lines += 1
            if not ids:
                report.uncited_claims.append(line[:120])

    report.citations = len(all_ids)
    report.distinct_sources = len(set(all_ids))
    return report
