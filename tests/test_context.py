"""Phase 2 must refuse to start on a missing, outdated or mismatched EDA profile."""

import json

import pytest

from discovery_chef.context import StaleProfileError, load_context
from discovery_chef.paths import EDA_PROFILE_PATH


def _profile_copy(tmp_path, **changes):
    profile = json.loads(EDA_PROFILE_PATH.read_text(encoding="utf-8"))
    profile.update(changes)
    path = tmp_path / "evidence_profile.json"
    path.write_text(json.dumps(profile), encoding="utf-8")
    return path


def test_current_profile_loads():
    ctx = load_context()
    assert ctx.excluded_interviews() == ["P06"]
    assert ctx.citable_snippets() == ["S01", "S02", "S03", "S04", "S05"]


def test_missing_profile(tmp_path):
    with pytest.raises(StaleProfileError, match="Run `uv run discovery-chef eda` first"):
        load_context(profile_path=tmp_path / "nope.json")


def test_profile_built_from_other_data(tmp_path):
    path = _profile_copy(tmp_path, data_sha256={"interviews/P01.md": "0" * 64})
    with pytest.raises(StaleProfileError, match="different data"):
        load_context(profile_path=path)


def test_profile_with_another_schema_version(tmp_path):
    path = _profile_copy(tmp_path, schema_version=999)
    with pytest.raises(StaleProfileError, match="schema version 999"):
        load_context(profile_path=path)
