"""Analyst coding must stay grounded: every quote verbatim, every ID real."""

import pytest

from discovery_chef.dataset import load_dataset
from discovery_chef.eda.annotations import (
    HOUSEHOLD_TYPES,
    IDEA_CLAIMS,
    INTERVIEW_CODING,
    SNIPPET_CHECKS,
    WTP_CATEGORIES,
)


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def _quotes(coding):
    yield from coding.fit_quotes
    yield from (q for q in (coding.shopping_quote, coding.tools_quote, coding.wtp.quote) if q)
    for issue in coding.issues:
        yield from issue.quotes


def test_every_interview_is_coded(dataset):
    assert set(INTERVIEW_CODING) == set(dataset.interviews)


@pytest.mark.parametrize("interview_id", sorted(INTERVIEW_CODING))
def test_quotes_are_verbatim(dataset, interview_id):
    interview = dataset.interviews[interview_id]
    missing = [q for q in _quotes(INTERVIEW_CODING[interview_id]) if not interview.contains(q)]
    assert not missing, f"{interview_id}: quotes not found verbatim: {missing}"


def test_coded_values_are_valid():
    for coding in INTERVIEW_CODING.values():
        assert coding.household_type in HOUSEHOLD_TYPES
        assert coding.target_fit in {"in", "partial", "out"}
        assert coding.cooks_most_weeknights in {"yes", "partly", "no", "unclear"}
        assert coding.shopping_pattern in {"weekly", "daily", "ad_hoc", "unknown"}
        assert coding.wtp.category in WTP_CATEGORIES
        for issue in coding.issues:
            assert issue.severity in {"major", "minor"}
            assert issue.quotes


def test_target_fit_follows_the_definition():
    for coding in INTERVIEW_CODING.values():
        if coding.target_fit == "in":
            assert coding.household_size >= 2
        if coding.household_size < 2:
            assert coding.target_fit == "out"


def test_snippet_checks_reference_real_ids(dataset):
    known = set(dataset.interviews) | set(dataset.snippets)
    for snippet_id, check in SNIPPET_CHECKS.items():
        assert snippet_id in dataset.snippets
        assert set(check.conflicts_with) <= known


def test_idea_claims_are_verbatim(dataset):
    for claim in IDEA_CLAIMS.values():
        assert claim in dataset.idea.text
