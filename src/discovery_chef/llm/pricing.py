"""Token prices and per-call cost for Gemini models.

USD per million tokens, Gemini API paid tier, from ai.google.dev/gemini-api/docs/pricing
(read 2026-10-13; prompts here are far below the 200k-token tier). Thinking tokens are
billed as output. Cached tokens come from Gemini's implicit caching: no write charge, and
reads are billed at the cache rate. On the free tier the real cost is $0; we report list
price so runs stay comparable.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float


PRICES: dict[str, Price] = {
    "gemini-3.8-flash": Price(input=0.75, output=3.75, cache_read=0.075),
    "gemini-3.6-flash": Price(input=0.75, output=3.75, cache_read=0.075),
    "gemini-3.5-flash-lite": Price(input=0.30, output=2.50, cache_read=0.03),
    "gemini-3.1-flash-lite": Price(input=0.25, output=1.50, cache_read=0.025),
    "gemini-3.1-pro-preview": Price(input=2.00, output=12.00, cache_read=0.20),
    "gemini-3-flash-preview": Price(input=0.50, output=3.00, cache_read=0.05),
    "gemini-2.5-pro": Price(input=1.25, output=10.00, cache_read=0.125),
    "gemini-2.5-flash": Price(input=0.30, output=2.50, cache_read=0.03),
}


LOCAL = Price(input=0.0, output=0.0, cache_read=0.0)


def price_for(model: str) -> Price | None:
    if model.startswith("ollama:"):  # runs on your own machine
        return LOCAL
    name = model.removeprefix("models/")
    if name in PRICES:
        return PRICES[name]
    # Versioned names such as "gemini-3.8-flash-001" price like their base model.
    matches = [key for key in PRICES if name.startswith(key)]
    return PRICES[max(matches, key=len)] if matches else None


@dataclass(frozen=True)
class TokenUsage:
    model: str
    input_tokens: int = 0  # uncached prompt tokens
    output_tokens: int = 0  # visible output + thinking
    cache_read_tokens: int = 0
    thinking_tokens: int = 0  # already included in output_tokens; reported separately

    @property
    def cost_usd(self) -> float | None:
        price = price_for(self.model)
        if price is None:
            return None
        return (self.input_tokens * price.input + self.output_tokens * price.output
                + self.cache_read_tokens * price.cache_read) / 1_000_000


def usage_from_response(response, model: str) -> TokenUsage:
    """Billable tokens from `usage_metadata`.

    `prompt_token_count` includes cached tokens, so they are subtracted to get the tokens
    billed at the full input rate.
    """
    meta = response.usage_metadata
    prompt = (meta.prompt_token_count or 0) + (meta.tool_use_prompt_token_count or 0)
    cached = meta.cached_content_token_count or 0
    thinking = meta.thoughts_token_count or 0
    return TokenUsage(
        model=model,
        input_tokens=prompt - cached,
        output_tokens=(meta.candidates_token_count or 0) + thinking,
        cache_read_tokens=cached,
        thinking_tokens=thinking,
    )
