"""Calling models: structured outputs, tool loops, cost and latency tracking.

Agents depend only on the `LLM` interface; `create_llm` picks the provider.
    gemini  Google's Gemini API (paid or free tier, needs GEMINI_API_KEY)
    ollama  open models running locally through Ollama (free, no key, slower)
"""

from discovery_chef.llm.base import (
    DEFAULT_EFFORT,
    DEFAULT_MODEL,
    DEFAULT_MODELS,
    EFFORTS,
    LLM,
    PROVIDERS,
    Conversation,
    LLMConfig,
    LLMError,
    QuotaExhaustedError,
    RefusalError,
    Tool,
    ToolOutput,
    TruncatedError,
    UserTurn,
)
from discovery_chef.llm.tracking import RunTracker


def create_llm(config: LLMConfig, tracker: RunTracker) -> LLM:
    if config.provider == "gemini":
        from discovery_chef.llm.gemini import GeminiClient

        return GeminiClient(config, tracker)
    if config.provider == "ollama":
        from discovery_chef.llm.ollama import OllamaClient

        return OllamaClient(config, tracker)
    raise ValueError(f"unknown provider {config.provider!r}; choose from {PROVIDERS}")


__all__ = [
    "DEFAULT_EFFORT", "DEFAULT_MODEL", "DEFAULT_MODELS", "EFFORTS", "LLM", "PROVIDERS",
    "Conversation", "LLMConfig", "LLMError", "QuotaExhaustedError", "RefusalError",
    "RunTracker", "Tool", "ToolOutput", "TruncatedError", "UserTurn", "create_llm",
]
