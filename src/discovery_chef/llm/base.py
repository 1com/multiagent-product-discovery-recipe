"""Provider-neutral pieces shared by every model client (Gemini, Ollama).

Agents only see the `LLM` interface: give it a conversation, an output type and optional
tools, get back a validated Pydantic object. How a provider calls its model, executes
tools and enforces the output format is its own business.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Protocol, TypeVar

from pydantic import BaseModel

from discovery_chef.llm.tracking import RunTracker, ToolRecord

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODELS = {"gemini": "gemini-3.8-flash", "ollama": "qwen3.5:4b"}
DEFAULT_EFFORT = {"gemini": "medium", "ollama": "low"}  # local CPU runs: keep thinking off
PROVIDERS = tuple(DEFAULT_MODELS)
DEFAULT_MODEL = DEFAULT_MODELS["gemini"]
EFFORTS = ("low", "medium", "high")

BUDGET_SPENT = ("You have used all {budget} rounds of tool calls. Do not call any more tools: "
                "give your final answer now, based on what you have already checked.")


class LLMError(RuntimeError):
    pass


class RefusalError(LLMError):
    pass


class TruncatedError(LLMError):
    pass


class QuotaExhaustedError(LLMError):
    """The API asked us to wait longer than is worth waiting (e.g. a daily quota)."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str = "gemini"
    model: str = DEFAULT_MODEL
    effort: str = "medium"  # low | medium | high (thinking level)
    max_tokens: int = 32000  # output ceiling per call, thinking included
    max_tool_rounds: int = 12
    num_ctx: int = 32768  # Ollama only: context window (Ollama's own default is 4096)


@dataclass(frozen=True)
class ToolOutput:
    text: str
    ids: list[str] = field(default_factory=list)  # source IDs returned, for the trace


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict  # JSON Schema of the arguments
    handler: Callable[[dict], ToolOutput]


@dataclass(frozen=True)
class UserTurn:
    text: str


@dataclass
class Conversation:
    """System prompt plus turns. User turns are provider-neutral `UserTurn`s; each client
    appends its model's turns in its own native format (Gemini's must stay unchanged so
    their thought signatures survive). A conversation is only ever used by one client."""

    system: str
    messages: list = field(default_factory=list)

    def say(self, text: str) -> Conversation:
        self.messages.append(UserTurn(text))
        return self


class LLM(Protocol):
    config: LLMConfig

    def run(self, *, agent: str, step: str, conversation: Conversation, output_type: type[T],
            tools: Sequence[Tool] = ()) -> T: ...


def run_tool(tracker: RunTracker, agent: str, tools: dict[str, Tool], name: str,
             args: dict) -> dict:
    """Execute one tool call and record it. Errors go back to the model, not up the stack."""
    tool = tools.get(name)
    try:
        if tool is None:
            raise ValueError(f"unknown tool {name!r}")
        output = tool.handler(args)
        tracker.add_tool(ToolRecord(agent, name, args, output.ids))
        return {"result": output.text}
    except Exception as error:
        tracker.add_tool(ToolRecord(agent, name, args, [], is_error=True))
        return {"error": str(error)}


def parse_output[M: BaseModel](agent: str, text: str, output_type: type[M]) -> M:
    try:
        return output_type.model_validate_json(text or "")
    except ValueError as error:
        raise LLMError(f"{agent}: output did not match {output_type.__name__}: {error}"
                       ) from error
