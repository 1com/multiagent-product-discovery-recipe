from discovery_chef.agents.contracts import BRIEF_SECTIONS
from discovery_chef.citations import check_brief, citation_ids


def _with(passing_brief, section_index, line):
    """Insert `line` at the end of the given section of the passing brief."""
    lines = passing_brief.splitlines()
    heading = BRIEF_SECTIONS[section_index]
    at = next(i for i, text in enumerate(lines) if text.startswith(heading)) + 2
    return "\n".join(lines[:at] + [line] + lines[at:])


def test_passing_brief(ctx, passing_brief):
    report = check_brief(passing_brief, ctx)
    assert report.passed, report.render()
    assert report.verified_quotes == 1
    assert report.coverage == 1.0
    assert report.unverified_numbers == []


def test_citation_parsing():
    line = "Text [P02:t4, P10:t2; C:ZeroWaste Kitchen] and a [link](http://x) [S05] [UNSUPPORTED]"
    assert citation_ids(line) == ["P02:t4", "P10:t2", "C:ZeroWaste Kitchen", "S05",
                                  "UNSUPPORTED"]


def test_unknown_ids_are_blocking(ctx, passing_brief):
    brief = _with(passing_brief, 2, "A claim that cites sources that do not exist at all "
                  "anywhere in the data [P11:t2, C:FakeApp].")
    report = check_brief(brief, ctx)
    assert report.unknown_ids == ["P11:t2", "C:FakeApp"]
    assert not report.passed


def test_misquote_is_blocking(ctx, passing_brief):
    brief = _with(passing_brief, 2, 'They said "We bought parsley twice in one week" '
                  "which is a duplicate purchase story [P02:t4].")
    report = check_brief(brief, ctx)
    assert len(report.misquotes) == 1
    assert not report.passed


def test_excluded_interview_citation(ctx, passing_brief):
    cited = _with(passing_brief, 2, "Busy parents would definitely pay for automatic "
                  "planning according to this interview [P06:t9].")
    assert check_brief(cited, ctx).excluded_citations
    hedged = _with(passing_brief, 3, "The leading interview is excluded and not used as "
                   "evidence for any claim in this brief [P06].")
    assert not check_brief(hedged, ctx).excluded_citations


def test_unusable_snippet_needs_a_caveat(ctx, passing_brief):
    brief = _with(passing_brief, 4, "Nearly all households would pay for automated meal "
                  "planning, at 97% [S08].")
    assert check_brief(brief, ctx).weak_snippet_citations


def test_numbers_must_trace_to_a_source(ctx, passing_brief):
    brief = _with(passing_brief, 4, "Households waste EUR 42 a week on food they never "
                  "eat, according to the panel [S01].")
    report = check_brief(brief, ctx)
    assert any("EUR 42" in n for n in report.unverified_numbers)
    words = _with(passing_brief, 3, "One participant said they would pay EUR 30 a month "
                  "after a holiday fridge disaster [P08:t9].")
    assert not check_brief(words, ctx).unverified_numbers  # "thirty euros" in P08


def test_uncited_claims_lower_coverage(ctx, passing_brief):
    brief = _with(passing_brief, 1, "Most households in the target segment want an app "
                  "that plans every dinner for them automatically.")
    report = check_brief(brief, ctx)
    assert report.uncited_claims and report.coverage < 1.0


def test_missing_sections(ctx, passing_brief):
    brief = passing_brief.replace("## 7. What to test next", "## Next steps")
    assert check_brief(brief, ctx).missing_sections == ["## 7. What to test next"]


def test_escaped_line_breaks_are_decoded(ctx, passing_brief):
    from discovery_chef.agents.contracts import DiscoveryBrief

    escaped = passing_brief.replace("\n", "\\n")
    brief = DiscoveryBrief(recommendation="test_further", one_line_rationale="r",
                           markdown=escaped)
    assert brief.markdown == passing_brief
    assert check_brief(brief.markdown, ctx).passed


def test_internal_ids_are_not_valid_citations(ctx, passing_brief):
    brief = _with(passing_brief, 2, "Food waste is a strong, repeated problem across the "
                  "usable interviews in this sample [F16, A1, R2, P02:t4].")
    report = check_brief(brief, ctx)
    assert report.unknown_ids == ["F16", "A1", "R2"]
    assert not report.passed


def test_idea_brief_is_a_valid_citation(ctx, passing_brief):
    brief = _with(passing_brief, 1, 'The idea brief targets households that "cook at home '
                  'on most weeknights" and want less waste [idea_brief].')
    report = check_brief(brief, ctx)
    assert report.passed and report.unknown_ids == [] and report.verified_quotes == 2


def test_dates_must_match_the_data(ctx, passing_brief):
    wrong = _with(passing_brief, 4, "PlanPlate was last verified on 2004-11-05, so its "
                  "row is stale and may be outdated [C:PlanPlate].")
    report = check_brief(wrong, ctx)
    assert report.wrong_dates and not report.passed
    right = wrong.replace("2004-11-05", "2024-11-05")
    assert check_brief(right, ctx).passed


def test_proposals_marked_unsupported_skip_the_number_check(ctx, passing_brief):
    brief = _with(passing_brief, 6, "Recruit 20 households and succeed if 70 percent keep "
                  "their inventory current for a week [UNSUPPORTED].")
    assert check_brief(brief, ctx).unverified_numbers == []


def test_p06_may_be_cited_as_a_method_problem(ctx, passing_brief):
    brief = _with(passing_brief, 3, "Interview P06 was excluded with zero weight because "
                  "nine of its ten questions were leading [P06].")
    assert check_brief(brief, ctx).excluded_citations == []
