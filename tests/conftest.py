import pytest

from discovery_chef.context import load_context

PASSING_BRIEF = """# PantryPal discovery brief

## 1. Recommendation
Test further before building [P02:t8].

## 2. Who the users are
Couples without children who both shop describe buying the same items twice in one week \
[P02:t4].

## 3. Problems that are real
One couple said "We bought basil twice in one week because each of us thought we were out" \
and both bunches went bad [P02:t4].

## 4. What the evidence says
Duplicate buying appears as concrete past behaviour in two usable interviews, which is a \
moderate signal [P02:t4, P04:t4].

## 5. Competitors and market
The median stated willingness to pay for a cooking app is EUR 3.50 per month according to \
the pricing study [S05].

## 6. Risks and open assumptions
Participants say they will quit if they must type in their whole pantry, so inventory \
upkeep is the riskiest assumption [P02:t8, P05:t8].

## 7. What to test next
Run a one-week concierge test of photo-based inventory with ten households that cook most \
nights and count how many keep it current [P02:t8].

## 8. Unsupported or weak claims
The 97% figure comes from a blog and is unreliable, so it is not used [S08].
"""


@pytest.fixture(autouse=True)
def no_real_api(monkeypatch, tmp_path):
    """Tests must never reach a model (Gemini API or local Ollama) or read the real .env."""
    from discovery_chef import cli
    from discovery_chef.llm import gemini, ollama

    def refuse(*args, **kwargs):
        raise RuntimeError("tests must not call a real model (Gemini or Ollama)")

    monkeypatch.setattr(gemini, "make_client", refuse)
    monkeypatch.setattr(ollama, "_post_json", refuse)
    monkeypatch.setattr(cli, "ENV_FILE", tmp_path / "no.env")
    for name in cli.CREDENTIAL_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(scope="session")
def ctx():
    return load_context()


@pytest.fixture
def passing_brief():
    return PASSING_BRIEF
