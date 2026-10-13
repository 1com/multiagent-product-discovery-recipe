import json

import pytest

from discovery_chef.eda import build_profile, write_outputs
from discovery_chef.eda.codebook import THEMES
from discovery_chef.eda.interviews import leading_flags
from discovery_chef.paths import DATA_DIR


@pytest.fixture(scope="module")
def profile():
    return build_profile()


def test_leading_question_detection():
    assert leading_flags("Wouldn't it be amazing if an app just planned all your meals?")
    assert leading_flags("Last Tuesday must have been stressful, wasn't it?")
    assert not leading_flags("Can you walk me through last Tuesday evening?")
    assert not leading_flags("Would you pay for something like that? What would feel fair?")


def test_only_p06_is_excluded(profile):
    metrics = profile.metrics.set_index("interview_id")
    assert list(metrics.index[metrics["evidence_tier"] == "excluded"]) == ["P06"]
    assert metrics.loc["P06", "leading_questions"] >= 5
    assert (metrics.drop("P06")["leading_questions"] == 0).all()


def test_out_of_target_interview_is_contrast_only(profile):
    metrics = profile.metrics.set_index("interview_id")
    assert metrics.loc["P07", "target_fit"] == "out"
    assert metrics.loc["P07", "evidence_tier"] == "contrast_only"


def test_templated_requirement_has_no_own_words_support(profile):
    setup = profile.theme_support.set_index("theme").loc["fast_setup"]
    assert setup.raw_interviews == 5
    assert setup.non_templated_interviews == 0


def test_every_theme_is_reported(profile):
    assert set(profile.theme_support["theme"]) == {t.key for t in THEMES}


def test_competitor_checks(profile):
    competitors = profile.competitors.set_index("competitor")
    stale = set(competitors.index[competitors["freshness"] == "stale"])
    assert stale == {"PlanPlate", "ZeroWaste Kitchen"}
    assert "no source URL" in competitors.loc["WeekWise", "issues"]


def test_no_competitor_combines_inventory_and_weekly_plan(profile):
    caps = profile.capabilities
    assert not ((caps["knows_inventory"] == 1) & (caps["weekly_plan"] == 1)).any()


def test_snippet_reliability(profile):
    reliability = profile.snippets.set_index("snippet_id")["reliability"].to_dict()
    assert reliability["S06"] == reliability["S07"] == "unsupported"
    assert reliability["S08"] == "unreliable"
    assert reliability["S09"] == "stale"
    assert {reliability[s] for s in ("S01", "S02", "S03", "S05")} == {"usable"}


def test_findings_are_complete_and_cite_real_ids(profile):
    known = (set(profile.dataset.interviews) | set(profile.dataset.competitors)
             | set(profile.dataset.snippets))
    ids = [f.id for f in profile.findings]
    assert len(ids) == len(set(ids))
    assert {f.question for f in profile.findings} == {"Q1", "Q2", "Q3", "Q4", "Q5"}
    for finding in profile.findings:
        assert finding.so_the_agent_will.startswith("So the agent will"), finding.id
        assert set(finding.evidence) <= known, finding.id


def test_excluded_interviews_are_not_cited_as_problem_evidence(profile):
    f10 = next(f for f in profile.findings if f.id == "F10")
    assert "P06" not in f10.evidence
    assert "P06" not in f10.finding  # not in the evidence list, nor in the sentence


def test_outputs_are_deterministic(profile, tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    write_outputs(profile, first, figures=False)
    write_outputs(build_profile(), second, figures=False)
    for path in first.rglob("*"):
        if path.is_file():
            assert path.read_bytes() == (second / path.relative_to(first)).read_bytes(), path


def test_profile_json_contract(profile, tmp_path):
    write_outputs(profile, tmp_path, figures=False)
    data = json.loads((tmp_path / "evidence_profile.json").read_text())
    assert data["schema_version"] == 1
    assert data["as_of"] == "2026-09-14"
    assert data["interviews"]["P06"]["evidence_weight"] == 0
    assert all("so_the_agent_will" in f for f in data["findings"])
    assert set(data["market_snippets"]) == {f"S{i:02d}" for i in range(1, 10)}


def test_quotes_inside_findings_are_verbatim(profile):
    import re

    corpus = " ".join(
        path.read_text(encoding="utf-8") for path in sorted(DATA_DIR.rglob("*")) if path.is_file()
    )
    corpus = " ".join(corpus.split())
    checked = 0
    for finding in profile.findings:
        for quote in re.findall(r'"([^"]+)"', finding.finding):
            assert quote in corpus, f"{finding.id}: not found verbatim: {quote!r}"
            checked += 1
    assert checked >= 10  # the findings do quote the data; the check is not vacuous


def test_topic_scoped_issues_do_not_lower_the_weight(profile):
    p08 = profile.metrics.set_index("interview_id").loc["P08"]
    assert (p08.major_issues, p08.topic_caveats, p08.evidence_quality) == (0, 1, 1.0)


def test_planning_resistance_means_explicit_rejection(profile):
    support = profile.theme_support.set_index("theme")
    assert support.loc["planning_resistance", "interviews"] == ["P05"]
