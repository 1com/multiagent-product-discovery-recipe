"""Gemini provider: structured output, optional tools, tracked cost.

Each call goes through `client.models.generate_content` with:
- a Pydantic `response_schema`, so every hand-off is validated JSON,
- `thinking_level` (Gemini 3 models always think; the level sets how much),
- the agent's tools as function declarations, executed here, never automatically by the
  SDK, so every tool call is visible and recorded. Gemini 3 accepts tools and a response
  schema in the same request.

Conversations are append-only: the model's turns are stored exactly as returned, which
keeps Gemini's thought signatures intact (they must be sent back unchanged).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from google.genai import types

from discovery_chef.llm.base import (
    BUDGET_SPENT,
    Conversation,
    LLMConfig,
    LLMError,
    QuotaExhaustedError,
    RefusalError,
    T,
    Tool,
    TruncatedError,
    UserTurn,
    parse_output,
    run_tool,
)
from discovery_chef.llm.pricing import usage_from_response
from discovery_chef.llm.tracking import RunTracker

# Finish reasons that mean a safety system blocked the answer.
BLOCKED = {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "RECITATION"}


# Rate limits (HTTP 429) are handled here rather than by the SDK's retry, because the
# error says how long to wait: seconds for a per-minute limit, hours for a daily quota.
MAX_RATE_LIMIT_WAIT_S = 90
MAX_RATE_LIMIT_RETRIES = 5


def _declaration(tool: Tool) -> types.FunctionDeclaration:
    return types.FunctionDeclaration(name=tool.name, description=tool.description,
                                     parameters_json_schema=tool.input_schema)


def _contents(conversation: Conversation) -> list:
    """Neutral user turns become Gemini Content; model turns are already native."""
    return [types.Content(role="user", parts=[types.Part(text=m.text)])
            if isinstance(m, UserTurn) else m for m in conversation.messages]


def make_client():
    """Gemini client reading GEMINI_API_KEY.

    The SDK retries server errors with exponential backoff (5s, 10s, 20s ... capped at
    120s, about 6 minutes in total): "503 high demand" spikes can last minutes, and a
    batch run is better late than lost.
    """
    from google import genai

    # With tools plus a response schema, every tool round triggers a harmless SDK warning
    # ("non-text parts in the response"); we read function calls directly, so silence it.
    logging.getLogger("google_genai.types").setLevel(logging.ERROR)
    retry = types.HttpRetryOptions(attempts=8, initial_delay=5.0, max_delay=120.0,
                                   http_status_codes=[500, 502, 503, 504])
    return genai.Client(http_options=types.HttpOptions(timeout=600_000, retry_options=retry))


def retry_delay_s(error) -> float | None:
    """Seconds the API asks us to wait, from the RetryInfo detail of a 429 error."""
    details = error.details.get("error", error.details) if isinstance(error.details, dict) \
        else {}
    for detail in details.get("details", []) or []:
        delay = detail.get("retryDelay") if isinstance(detail, dict) else None
        if isinstance(delay, str) and delay.endswith("s"):
            try:
                return float(delay[:-1])
            except ValueError:
                return None
    return None


class GeminiClient:
    def __init__(self, config: LLMConfig, tracker: RunTracker, client=None):
        self.config = config
        self.tracker = tracker
        self._client = client or make_client()

    def run(self, *, agent: str, step: str, conversation: Conversation, output_type: type[T],
            tools: Sequence[Tool] = ()) -> T:
        """Complete the conversation's last user turn and return the parsed output.

        Tool calls are executed and fed back until the model answers. Every model turn and
        tool result is appended to `conversation.messages`, so a later `say()` + `run()`
        continues the same thread (used for revisions).
        """
        tool_map = {tool.name: tool for tool in tools}
        budget = self.config.max_tool_rounds
        for round_number in range(budget + 1):
            # After `budget` rounds of tool calls the model must answer: it is told so with
            # the last tool results, and the final request forbids further tool calls.
            forced = round_number == budget
            label = (step if round_number == 0 else
                     f"{step}/forced-answer" if forced else f"{step}/tool-round-{round_number}")
            response = self._call(agent, label, conversation, output_type, tools,
                                  allow_tools=not forced)
            conversation.messages.append(response.candidates[0].content)
            calls = response.function_calls or []
            if calls and not forced:
                parts = [self._run_tool(agent, tool_map, call) for call in calls]
                if round_number == budget - 1:
                    parts.append(types.Part(text=BUDGET_SPENT.format(budget=budget)))
                conversation.messages.append(types.Content(role="user", parts=parts))
                continue
            if calls:
                raise LLMError(f"{agent}: kept calling tools after its {budget}-round budget")
            return self._parse(agent, response, output_type)
        raise AssertionError("unreachable")

    def _call(self, agent, step, conversation, output_type, tools, allow_tools=True):
        config = types.GenerateContentConfig(
            system_instruction=conversation.system,
            response_mime_type="application/json",
            response_schema=output_type,
            thinking_config=types.ThinkingConfig(
                thinking_level=types.ThinkingLevel[self.config.effort.upper()]),
            max_output_tokens=self.config.max_tokens,
            tools=[types.Tool(function_declarations=[_declaration(t) for t in tools])]
            if tools else None,
            # Tools stay declared (the history contains their calls) but may not be called.
            tool_config=None if allow_tools or not tools else types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.NONE)),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        started = time.perf_counter()
        response = self._generate(agent, conversation, config)
        candidate = response.candidates[0] if response.candidates else None
        finish = _name(candidate.finish_reason) if candidate else None
        self.tracker.add_call(
            agent=agent, step=step, usage=usage_from_response(response, self.config.model),
            latency_s=time.perf_counter() - started, finish_reason=finish,
            model_version=getattr(response, "model_version", None),
        )
        if candidate is None or candidate.content is None:
            feedback = getattr(response, "prompt_feedback", None)
            reason = _name(getattr(feedback, "block_reason", None)) or finish or "no candidate"
            raise RefusalError(f"{agent}: request blocked ({reason})")
        if finish in BLOCKED:
            raise RefusalError(f"{agent}: answer blocked ({finish})")
        if finish == "MAX_TOKENS":
            raise TruncatedError(f"{agent}: hit max_tokens={self.config.max_tokens}; "
                                 "raise --max-tokens or lower --effort")
        if finish not in (None, "STOP", "FINISH_REASON_UNSPECIFIED"):
            raise LLMError(f"{agent}: generation stopped ({finish})")
        return response

    def _generate(self, agent, conversation, config):
        from google.genai import errors

        for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
            try:
                return self._client.models.generate_content(
                    model=self.config.model, contents=_contents(conversation), config=config)
            except errors.ClientError as error:
                if error.code != 429:
                    raise
                delay = retry_delay_s(error)
                if delay is None or delay > MAX_RATE_LIMIT_WAIT_S \
                        or attempt == MAX_RATE_LIMIT_RETRIES:
                    raise QuotaExhaustedError(
                        f"{agent}: quota for {self.config.model} exhausted"
                        + (f" (the API says retry in {delay / 3600:.1f}h)" if delay else "")
                        + ". Free-tier daily quotas are per model and reset at midnight "
                        "Pacific time; try another --model or enable billing in AI Studio."
                    ) from error
                time.sleep(delay + 1)
        raise AssertionError("unreachable")

    def _parse(self, agent: str, response, output_type: type[T]) -> T:
        if isinstance(response.parsed, output_type):
            return response.parsed
        # the SDK leaves `parsed` empty if its own parse fails; validate to say why
        return parse_output(agent, response.text, output_type)

    def _run_tool(self, agent: str, tool_map: dict[str, Tool], call) -> types.Part:
        response = run_tool(self.tracker, agent, tool_map, call.name, dict(call.args or {}))
        part = types.Part.from_function_response(name=call.name, response=response)
        part.function_response.id = call.id  # pairs the result with its call
        return part


def _name(value) -> str | None:
    """Enum or string to its plain name (e.g. FinishReason.STOP -> 'STOP')."""
    if value is None:
        return None
    return getattr(value, "name", None) or str(value)
