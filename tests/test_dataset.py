from datetime import date

import pytest

from discovery_chef.dataset import load_dataset, parse_interview, split_sentences


@pytest.fixture(scope="module")
def dataset():
    return load_dataset()


def test_counts(dataset):
    assert sorted(dataset.interviews) == [f"P{i:02d}" for i in range(1, 11)]
    assert len(dataset.competitors) == 7
    assert sorted(dataset.snippets) == [f"S{i:02d}" for i in range(1, 10)]


def test_every_interview_has_ten_question_answer_turns(dataset):
    for interview in dataset.interviews.values():
        assert len(interview.turns) == 10, interview.id
        assert all(turn.question and turn.answer for turn in interview.turns)


def test_research_date_is_last_interview(dataset):
    assert dataset.as_of == date(2026, 9, 14)


def test_target_customer_parsed(dataset):
    assert dataset.idea.target_customer.startswith("households of two or more people")


def test_missing_values_become_none(dataset):
    assert dataset.competitors["WeekWise"].source_url is None
    assert dataset.snippets["S06"].source_name is None
    assert dataset.snippets["S06"].year is None


def test_malformed_transcript_is_rejected(tmp_path):
    bad = tmp_path / "P99.md"
    bad.write_text("---\ninterview_id: P99\nparticipant_persona: x\ndate: 2026-01-01\n---\n"
                   "Interviewer: Hello?\nInterviewer: Anyone?\n")
    with pytest.raises(ValueError, match="two interviewer lines"):
        parse_interview(bad)


def test_split_sentences():
    assert split_sentences("Just me. Not really! Why? Fine") == (
        "Just me.", "Not really!", "Why?", "Fine")
