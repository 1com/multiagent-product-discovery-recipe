"""The Gemini client against a scripted fake of the Gemini SDK (no network).

The fake returns real google-genai `Content` / `Part` objects, so history handling and
thought signatures are tested against the SDK's actual types.
"""

from types import SimpleNamespace

import pytest
from google.genai import types
from pydantic import BaseModel

from discovery_chef.llm import (
    Conversation,
    LLMConfig,
    LLMError,
    RefusalError,
    RunTracker,
    Tool,
    ToolOutput,
    TruncatedError,
)
from discovery_chef.llm import gemini as client_module
from discovery_chef.llm.gemini import GeminiClient
from discovery_chef.llm.pricing import TokenUsage, price_for, usage_from_response


class Answer(BaseModel):
    text: str


def usage(prompt=100, output=50, cached=0, thoughts=0):
    return types.GenerateContentResponseUsageMetadata(
        prompt_token_count=prompt, candidates_token_count=output,
        cached_content_token_count=cached, thoughts_token_count=thoughts)


def response(parts, finish="STOP", parsed=None, text=None, use=None):
    calls = [p.function_call for p in parts if p.function_call]
    return SimpleNamespace(
        candidates=[SimpleNamespace(content=types.Content(role="model", parts=parts),
                                    finish_reason=types.FinishReason[finish])],
        function_calls=calls or None, parsed=parsed, text=text,
        usage_metadata=use or usage(), prompt_feedback=None,
        model_version="gemini-3.8-flash-001")


def call_part(name, args, call_id="call-1"):
    return types.Part(function_call=types.FunctionCall(id=call_id, name=name, args=args))


class FakeGenAI:
    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, *, model, contents, config):
        self.requests.append({"model": model, "contents": list(contents), "config": config})
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_client(responses, **config):
    tracker = RunTracker()
    fake = FakeGenAI(responses)
    return GeminiClient(LLMConfig(**config), tracker, client=fake), fake, tracker


def echo_tool():
    return Tool("echo", "Echo the input.", {"type": "object", "properties": {
        "word": {"type": "string"}}, "required": ["word"], "additionalProperties": False},
        lambda args: ToolOutput(f"echo: {args['word']}", ["P01:t1"]))


def test_tool_loop_then_structured_answer():
    thought = types.Part(text="", thought=True, thought_signature=b"sig")
    llm, fake, tracker = make_client([
        response([thought, call_part("echo", {"word": "hi"})]),
        response([types.Part(text='{"text": "done"}')], parsed=Answer(text="done")),
    ])
    conversation = Conversation(system="sys").say("go")
    result = llm.run(agent="a", step="s", conversation=conversation, output_type=Answer,
                     tools=[echo_tool()])

    assert result == Answer(text="done")
    first = fake.requests[0]["config"]
    assert first.response_schema is Answer and first.response_mime_type == "application/json"
    assert first.thinking_config.thinking_level == types.ThinkingLevel.MEDIUM
    assert first.system_instruction == "sys"
    assert first.automatic_function_calling.disable is True
    assert first.tools[0].function_declarations[0].name == "echo"
    # the second request replays the model turn untouched (thought signature intact),
    # then the tool result paired to its call by id
    user, model_turn, tool_turn = fake.requests[1]["contents"]
    assert model_turn.parts[0].thought_signature == b"sig"
    result_part = tool_turn.parts[0].function_response
    assert (result_part.id, result_part.response) == ("call-1", {"result": "echo: hi"})
    assert [c.step for c in tracker.calls] == ["s", "s/tool-round-1"]
    assert tracker.tools[0].result_ids == ["P01:t1"]
    assert len(conversation.messages) == 4  # user, model, tool result, final model


def test_tool_errors_are_reported_to_the_model():
    llm, fake, tracker = make_client([
        response([call_part("missing_tool", {})]),
        response([types.Part(text="{}")], parsed=Answer(text="ok")),
    ])
    llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
            output_type=Answer, tools=[echo_tool()])
    returned = fake.requests[1]["contents"][2].parts[0].function_response.response
    assert "unknown tool" in returned["error"]
    assert tracker.tools[0].is_error


def test_blocked_and_truncated_answers_raise():
    llm, _, tracker = make_client([response([types.Part(text="")], finish="SAFETY")])
    with pytest.raises(RefusalError):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)
    assert len(tracker.calls) == 1  # failed calls are still billed and tracked

    llm, _, _ = make_client([response([types.Part(text='{"te')], finish="MAX_TOKENS")])
    with pytest.raises(TruncatedError):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)

    blocked_prompt = SimpleNamespace(
        candidates=[], function_calls=None, parsed=None, text=None, usage_metadata=usage(),
        prompt_feedback=SimpleNamespace(block_reason=types.BlockedReason.SAFETY),
        model_version=None)
    llm, _, _ = make_client([blocked_prompt])
    with pytest.raises(RefusalError, match="SAFETY"):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)


def test_output_is_validated_when_the_sdk_did_not_parse_it():
    llm, _, _ = make_client([response([types.Part(text='{"text": "x"}')],
                                      text='{"text": "x"}')])
    result = llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                     output_type=Answer)
    assert result == Answer(text="x")

    llm, _, _ = make_client([response([types.Part(text='{"wrong": 1}')], text='{"wrong": 1}')])
    with pytest.raises(LLMError, match="did not match Answer"):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)


def test_effort_sets_the_thinking_level():
    llm, fake, _ = make_client([response([types.Part(text="{}")], parsed=Answer(text="x"))],
                               effort="high", model="gemini-3.1-pro-preview")
    llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"), output_type=Answer)
    assert fake.requests[0]["model"] == "gemini-3.1-pro-preview"
    assert fake.requests[0]["config"].thinking_config.thinking_level == types.ThinkingLevel.HIGH


def test_billable_tokens_split_cache_and_thinking():
    use = usage_from_response(SimpleNamespace(usage_metadata=usage(
        prompt=1000, output=200, cached=400, thoughts=300)), "gemini-3.8-flash")
    assert (use.input_tokens, use.cache_read_tokens) == (600, 400)
    assert (use.output_tokens, use.thinking_tokens) == (500, 300)
    # 600 in at $0.75/M + 500 out at $3.75/M + 400 cached at $0.075/M
    assert use.cost_usd == pytest.approx((600 * 0.75 + 500 * 3.75 + 400 * 0.075) / 1e6)


def test_price_lookup():
    assert price_for("models/gemini-3.8-flash") == price_for("gemini-3.8-flash")
    assert price_for("gemini-3.8-flash-001") == price_for("gemini-3.8-flash")
    assert TokenUsage("unknown-model", input_tokens=1).cost_usd is None


def test_tracker_summary_aggregates_per_agent():
    tracker = RunTracker()
    for agent in ("a", "a", "b"):
        tracker.add_call(agent=agent, step="s", usage=TokenUsage("gemini-3.8-flash", 100, 10),
                         latency_s=1.5, finish_reason="STOP")
    tracker.finish()
    summary = tracker.summary()
    assert summary["per_agent"]["a"]["calls"] == 2
    assert summary["totals"]["calls"] == 3
    assert summary["totals"]["model_time_s"] == pytest.approx(4.5)


def rate_limited(retry_after: str):
    from google.genai import errors

    return errors.ClientError(429, {"error": {
        "code": 429, "message": "Quota exceeded", "status": "RESOURCE_EXHAUSTED",
        "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo",
                     "retryDelay": retry_after}]}})


def test_short_rate_limits_are_waited_out(monkeypatch):
    slept = []
    monkeypatch.setattr(client_module.time, "sleep", slept.append)
    llm, fake, _ = make_client([rate_limited("2s"),
                                response([types.Part(text="{}")], parsed=Answer(text="x"))])
    llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"), output_type=Answer)
    assert slept == [3.0] and len(fake.requests) == 2


def test_daily_quota_fails_fast(monkeypatch):
    slept = []
    monkeypatch.setattr(client_module.time, "sleep", slept.append)
    llm, fake, tracker = make_client([rate_limited("54368s")])
    with pytest.raises(client_module.QuotaExhaustedError, match="15.1h"):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)
    assert slept == [] and len(fake.requests) == 1 and tracker.calls == []


def test_tool_budget_forces_a_final_answer():
    endless = [response([call_part("echo", {"word": str(i)}, call_id=f"c{i}")])
               for i in range(2)]
    final = response([types.Part(text='{"text": "verdict"}')], parsed=Answer(text="verdict"))
    llm, fake, tracker = make_client([*endless, final], max_tool_rounds=2)
    result = llm.run(agent="critic", step="review-0", conversation=Conversation("s").say("go"),
                     output_type=Answer, tools=[echo_tool()])
    assert result == Answer(text="verdict")
    # the last tool results carry the notice; the final request forbids tool calls
    notice = fake.requests[2]["contents"][-1].parts[-1].text
    assert "Do not call any more tools" in notice
    assert fake.requests[0]["config"].tool_config is None
    mode = fake.requests[2]["config"].tool_config.function_calling_config.mode
    assert mode == types.FunctionCallingConfigMode.NONE
    assert [c.step for c in tracker.calls][-1] == "review-0/forced-answer"


def test_tool_calls_after_the_budget_still_fail():
    endless = [response([call_part("echo", {"word": str(i)}, call_id=f"c{i}")])
               for i in range(3)]
    llm, _, _ = make_client(endless, max_tool_rounds=2)
    with pytest.raises(LLMError, match="kept calling tools"):
        llm.run(agent="critic", step="r", conversation=Conversation("s").say("go"),
                output_type=Answer, tools=[echo_tool()])
