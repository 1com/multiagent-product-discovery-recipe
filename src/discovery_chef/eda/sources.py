"""Trust and freshness checks for competitor rows and market snippets."""

from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlparse

import pandas as pd

from discovery_chef.dataset import Competitor, MarketSnippet
from discovery_chef.eda.annotations import SNIPPET_CHECKS
from discovery_chef.eda.codebook import CAPABILITIES

# Competitor rows: days since last_verified, relative to the research date.
COMPETITOR_AGING_DAYS = 180
COMPETITOR_STALE_DAYS = 365
# Market snippets: years since publication, relative to the research year.
SNIPPET_AGING_YEARS = 3
SNIPPET_STALE_YEARS = 5

_PRICE = re.compile(r"EUR\s*(\d+(?:\.\d+)?)\s*/\s*(month|year)", re.IGNORECASE)
_ONE_OFF = re.compile(r"EUR\s*(\d+(?:\.\d+)?)\s*one-off", re.IGNORECASE)
_PLACEHOLDER_TLDS = (".example", ".test", ".invalid")


def competitor_profile(competitors: dict[str, Competitor], as_of: date) -> pd.DataFrame:
    rows = []
    for c in competitors.values():
        issues = []
        days = (as_of - c.last_verified).days if c.last_verified else None
        if days is None:
            freshness = "unknown"
            issues.append("no last_verified date")
        elif days > COMPETITOR_STALE_DAYS:
            freshness = "stale"
            issues.append(f"last verified {days} days before the research date")
        elif days > COMPETITOR_AGING_DAYS:
            freshness = "aging"
        else:
            freshness = "current"

        parsed = urlparse(c.source_url) if c.source_url else None
        if parsed is None:
            issues.append("no source URL")
        elif parsed.path in ("", "/"):
            issues.append("source is a home page, not a pricing page")

        monthly = [float(v) if unit == "month" else round(float(v) / 12, 2)
                   for v, unit in _PRICE.findall(c.pricing)]
        one_off = [float(v) for v in _ONE_OFF.findall(c.pricing)]
        rows.append({
            "competitor": c.name,
            "positioning": c.positioning,
            "target_user": c.target_user,
            "pricing": c.pricing,
            "has_free_tier": bool(re.search(r"\bfree\b", c.pricing, re.IGNORECASE)),
            "lowest_paid_eur_month": min(monthly) if monthly else None,
            "one_off_eur": one_off[0] if one_off else None,
            "last_verified": c.last_verified.isoformat() if c.last_verified else None,
            "days_since_verified": days,
            "freshness": freshness,
            "source_url": c.source_url,
            # Synthetic dataset: placeholder URLs cannot be followed, so cite the row.
            "url_is_placeholder": bool(parsed and parsed.hostname
                                       and parsed.hostname.endswith(_PLACEHOLDER_TLDS)),
            "issues": issues,
        })
    return pd.DataFrame(rows)


def capability_matrix(competitors: dict[str, Competitor]) -> pd.DataFrame:
    """Which parts of the PantryPal pitch each competitor already offers (1 = yes)."""
    rows = {}
    for c in competitors.values():
        text = " ".join((c.positioning, *c.key_features))
        rows[c.name] = {key: int(bool(pattern.search(text)))
                        for key, (_, pattern) in CAPABILITIES.items()}
    return pd.DataFrame.from_dict(rows, orient="index")[list(CAPABILITIES)]


def snippet_profile(snippets: dict[str, MarketSnippet], as_of: date) -> pd.DataFrame:
    rows = []
    for s in snippets.values():
        issues = []
        if not s.source_name:
            issues.append("no source")
        elif "blog" in s.source_name.lower():
            issues.append("blog, not primary research")
        if not s.year:
            issues.append("no year")
        age = as_of.year - s.year if s.year else None
        if age is not None and age > SNIPPET_STALE_YEARS:
            issues.append(f"{age} years old")
        elif age is not None and age >= SNIPPET_AGING_YEARS:
            issues.append(f"{age} years old (aging)")
        check = SNIPPET_CHECKS.get(s.id)
        if check:
            issues.append(f"{check.kind}: {check.note}")
        rows.append({
            "snippet_id": s.id,
            "claim": s.claim,
            "stat": s.stat,
            "source_name": s.source_name,
            "year": s.year,
            "age_years": age,
            "reliability": _snippet_reliability(s, age, check),
            "issues": issues,
        })
    return pd.DataFrame(rows).astype({"year": "Int64", "age_years": "Int64"})


def _snippet_reliability(s: MarketSnippet, age: int | None, check) -> str:
    """usable / usable_with_caveat / unsupported / unreliable / stale."""
    if not s.source_name:
        return "unsupported"
    if (check and check.kind == "implausible") or "blog" in s.source_name.lower():
        return "unreliable"
    if age is not None and age > SNIPPET_STALE_YEARS:
        return "stale"
    if check or (age is not None and age >= SNIPPET_AGING_YEARS):
        return "usable_with_caveat"
    return "usable"
