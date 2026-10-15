"""The demo app renders every tab on a recorded run, headless (no browser, no API)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from discovery_chef.runs import RUNS_DIR

APP = Path(__file__).parents[1] / "src" / "discovery_chef" / "demo.py"


@pytest.mark.skipif(not any(RUNS_DIR.glob("*-agents/run.json")), reason="no recorded runs")
def test_demo_renders_a_recorded_run():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert [t.label for t in app.tabs] == ["Overview", "Agents", "Critic", "Final brief",
                                           "Comparison"]
    assert app.metric[0].label == "Recommendation"


def _help_page_script():
    import streamlit as st

    from discovery_chef import demo

    demo.PAGES["replay"] = st.Page(demo.replay_page, title="Run replay", default=True)
    demo.PAGES["help"] = st.Page(demo.help_page, title="Help: terms", url_path="help")
    st.navigation(list(demo.PAGES.values()), position="hidden")
    demo.help_page()


def test_help_page_opens_on_the_clicked_term():
    app = AppTest.from_function(_help_page_script, default_timeout=60)
    app.query_params["term"] = "criteria"
    app.run()
    assert not app.exception
    assert app.header[0].value == "Criteria (1-5)"  # the clicked term, shown first
    assert any(e.label == "Criteria (1-5)" and e.proto.expanded for e in app.expander)


def test_help_page_search_filters_the_terms():
    app = AppTest.from_function(_help_page_script, default_timeout=60).run()
    assert not app.header  # no term selected
    app.text_input[0].input("thinking").run()
    labels = {e.label for e in app.expander}
    assert "Output tokens" in labels and "Segment" not in labels


def test_every_linked_term_has_a_help_entry():
    import re

    from discovery_chef.glossary import GROUPS, TERMS, TERMS_BY_SLUG

    assert len(TERMS_BY_SLUG) == len(TERMS), "duplicate slugs"
    for term in TERMS:
        assert term.group in GROUPS, term.slug
        assert term.short and term.detail and term.example, term.slug
        missing = [r for r in term.related if r not in TERMS_BY_SLUG]
        assert not missing, f"{term.slug} relates to unknown terms {missing}"
    source = APP.read_text(encoding="utf-8")
    used = set(re.findall(r'(?:tip|term_link)\("([a-z_]+)"', source))
    for call in re.findall(r"terms_row\(([^)]*)\)", source):
        used |= set(re.findall(r'"([a-z_]+)"', call.split("label=")[0]))
    for mapping in re.findall(r"columns_help\(([^)]*)\)", source, flags=re.DOTALL):
        used |= set(re.findall(r'(?:=|: )"([a-z_]+)"', mapping))
    unknown = sorted(used - set(TERMS_BY_SLUG))
    assert used and not unknown, f"the demo links to terms with no help entry: {unknown}"
