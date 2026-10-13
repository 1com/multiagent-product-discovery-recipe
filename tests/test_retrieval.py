from discovery_chef.retrieval import tokenize


def test_one_passage_per_turn(ctx):
    assert len(ctx.index.passages) == 100
    assert ctx.index.by_id["P02:t4"].answer.startswith("We bought basil twice")


def test_search_finds_the_right_episode(ctx):
    hits = ctx.index.search("bought the same thing twice", k=3)
    assert hits[0].passage.id == "P02:t4"


def test_excluded_interviews_are_never_returned(ctx):
    query = "chaos school pickups homework work calls thirty minutes"
    assert all(h.passage.interview_id != "P06" for h in ctx.index.search(query, k=20))
    included = ctx.index.search(query, k=20, include_excluded=True)
    assert any(h.passage.interview_id == "P06" for h in included)


def test_passages_carry_evidence_metadata(ctx):
    setup = ctx.index.by_id["P02:t8"]
    assert setup.evidence_tier == "primary"
    assert "Setup has to be fast." in setup.templated_sentences
    rendered = setup.render()
    assert 'id="P02:t8"' in rendered and "Setup has to be fast." in rendered


def test_search_is_deterministic(ctx):
    first = [h.passage.id for h in ctx.index.search("pay euros", k=10)]
    assert first == [h.passage.id for h in ctx.index.search("pay euros", k=10)]


def test_tokenize_drops_stopwords_and_stems():
    assert tokenize("We were planning the plans") == ["plann", "plan"]


def test_source_lookup(ctx):
    assert "Budget-focused meal plans" in ctx.source_text("C:WeekWise")
    assert 'reliability="unreliable"' in ctx.source_text("S08")
    assert ctx.source_text("P99:t1") is None
