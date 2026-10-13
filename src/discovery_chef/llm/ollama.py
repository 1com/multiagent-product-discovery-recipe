"""Ollama provider: open models running locally, free, no API key.

Talks to Ollama's native /api/chat (stdlib HTTP, no extra dependency). Small local models
need more help than Gemini, so each call has two phases:
1. Tools (if the agent has any): the model calls tools until it is ready to answer, or its
   round budget is spent. Tool results go back as `tool` messages.
2. Answer: one request with the output's JSON Schema in `format` (Ollama constrains the
   output to it) and in the prompt (so the model also sees the field descriptions). If the
   JSON still fails validation, the error is shown to the model once for a repair.

Ollama silently drops the start of a prompt longer than its context window, so prompts are
size-checked first and a too-small `num_ctx` fails loudly instead.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Sequence

from discovery_chef.llm.base import (
    BUDGET_SPENT,
    Conversation,
    LLMConfig,
    LLMError,
    T,
    Tool,
    TruncatedError,
    UserTurn,
    parse_output,
    run_tool,
)
from discovery_chef.llm.pricing import TokenUsage
from discovery_chef.llm.tracking import RunTracker

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
CHARS_PER_TOKEN = 3.2  # conservative: real text averages closer to 4
ANSWER_NOW = ("Now give your final answer as JSON only, matching this JSON Schema exactly "
              "(the descriptions say what each field must contain):\n{schema}")
REPAIR = ("That answer did not match the schema: {error}\nReturn the corrected JSON only.")


def _post_json(path: str, payload: dict | None = None, timeout: float = 7200) -> dict:
    url = f"{OLLAMA_HOST}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise LLMError(f"Ollama returned {error.code}: {error.read()[:300]!r}") from error
    except urllib.error.URLError as error:
        raise LLMError(f"cannot reach Ollama at {OLLAMA_HOST} ({error.reason}). "
                       "Is it running? Start it with `ollama serve`.") from error


def installed_models() -> list[str]:
    return [m["name"] for m in _post_json("/api/tags", timeout=10).get("models", [])]


def _message(entry) -> dict:
    return {"role": "user", "content": entry.text} if isinstance(entry, UserTurn) else entry


def _tool_spec(tool: Tool) -> dict:
    return {"type": "function", "function": {"name": tool.name, "description": tool.description,
                                             "parameters": tool.input_schema}}


class OllamaClient:
    def __init__(self, config: LLMConfig, tracker: RunTracker, post=None):
        self.config = config
        self.tracker = tracker
        self._post = post or (lambda payload: _post_json("/api/chat", payload))

    def run(self, *, agent: str, step: str, conversation: Conversation, output_type: type[T],
            tools: Sequence[Tool] = ()) -> T:
        if tools:
            self._use_tools(agent, step, conversation, tools)
        schema = output_type.model_json_schema()
        extra = [{"role": "user", "content": ANSWER_NOW.format(schema=json.dumps(schema))}]
        for attempt in range(2):
            label = f"{step}/answer" if attempt == 0 else f"{step}/repair"
            message = self._chat(agent, label, conversation, extra=extra, schema=schema)
            text = message.get("content", "")
            try:
                parsed = parse_output(agent, text, output_type)
            except LLMError as error:
                if attempt == 1:
                    raise
                extra = [*extra, {"role": "assistant", "content": text},
                         {"role": "user", "content": REPAIR.format(error=error)}]
                continue
            conversation.messages.append({"role": "assistant", "content": text})
            return parsed
        raise AssertionError("unreachable")

    def _use_tools(self, agent: str, step: str, conversation: Conversation,
                   tools: Sequence[Tool]) -> None:
        tool_map = {tool.name: tool for tool in tools}
        budget = self.config.max_tool_rounds
        for round_number in range(budget):
            label = step if round_number == 0 else f"{step}/tool-round-{round_number}"
            message = self._chat(agent, label, conversation, tools=tools)
            calls = message.get("tool_calls") or []
            conversation.messages.append({"role": "assistant",
                                          "content": message.get("content", ""),
                                          **({"tool_calls": calls} if calls else {})})
            if not calls:
                return
            for call in calls:
                function = call.get("function", {})
                args = function.get("arguments") or {}
                if isinstance(args, str):
                    args = json.loads(args or "{}")
                result = run_tool(self.tracker, agent, tool_map, function.get("name", ""), args)
                conversation.messages.append({"role": "tool", "tool_name": function.get("name"),
                                              "content": json.dumps(result, ensure_ascii=False)})
        conversation.messages.append(UserTurn(BUDGET_SPENT.format(budget=budget)))

    def _chat(self, agent: str, step: str, conversation: Conversation, *,
              tools: Sequence[Tool] = (), extra: Sequence[dict] = (),
              schema: dict | None = None) -> dict:
        messages = [{"role": "system", "content": conversation.system},
                    *(_message(m) for m in conversation.messages), *extra]
        self._check_size(agent, messages, tools)
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "think": self.config.effort != "low",
            "options": {"num_ctx": self.config.num_ctx, "num_predict": self.config.max_tokens},
        }
        if tools:
            payload["tools"] = [_tool_spec(t) for t in tools]
        if schema is not None:
            payload["format"] = schema
        started = time.perf_counter()
        data = self._post(payload)
        usage = TokenUsage(model=f"ollama:{self.config.model}",
                           input_tokens=data.get("prompt_eval_count") or 0,
                           output_tokens=data.get("eval_count") or 0)
        self.tracker.add_call(agent=agent, step=step, usage=usage,
                              latency_s=time.perf_counter() - started,
                              finish_reason=data.get("done_reason"), model_version=None)
        if data.get("done_reason") == "length":
            raise TruncatedError(f"{agent}: hit max_tokens={self.config.max_tokens}")
        return data.get("message") or {}

    def _check_size(self, agent: str, messages: list[dict], tools: Sequence[Tool]) -> None:
        chars = sum(len(str(m.get("content", ""))) for m in messages)
        chars += sum(len(json.dumps(_tool_spec(t))) for t in tools)
        estimate = int(chars / CHARS_PER_TOKEN)
        if estimate + self.config.max_tokens // 4 > self.config.num_ctx:
            raise TruncatedError(
                f"{agent}: the prompt (~{estimate} tokens) would not fit Ollama's context "
                f"window of {self.config.num_ctx}; raise --num-ctx (needs more memory)")
