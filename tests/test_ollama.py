"""The Ollama client against scripted /api/chat responses (no Ollama needed)."""

import json

import pytest
from pydantic import BaseModel

from discovery_chef.llm import (
    Conversation,
    LLMConfig,
    LLMError,
    RunTracker,
    Tool,
    ToolOutput,
    TruncatedError,
    UserTurn,
)
from discovery_chef.llm.ollama import OllamaClient


class Answer(BaseModel):
    text: str


def reply(content="", tool_calls=None, done_reason="stop"):
    message = {"role": "assistant", "content": content}
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"message": message, "done_reason": done_reason, "prompt_eval_count": 1000,
            "eval_count": 200}


def call(name, arguments):
    return {"function": {"name": name, "arguments": arguments}}


class FakeOllama:
    def __init__(self, replies):
        self.replies = list(replies)
        self.payloads = []

    def __call__(self, payload):
        self.payloads.append(json.loads(json.dumps(payload)))  # snapshot
        return self.replies.pop(0)


def make(replies, **config):
    fake = FakeOllama(replies)
    tracker = RunTracker()
    config = {"provider": "ollama", "model": "qwen3.5:4b", "effort": "low", **config}
    return OllamaClient(LLMConfig(**config), tracker, post=fake), fake, tracker


def echo_tool():
    return Tool("echo", "Echo the input.", {"type": "object", "properties": {
        "word": {"type": "string"}}, "required": ["word"], "additionalProperties": False},
        lambda args: ToolOutput(f"echo: {args['word']}", ["P01:t1"]))


def test_structured_answer_without_tools():
    llm, fake, tracker = make([reply('{"text": "hi"}')])
    conversation = Conversation("sys").say("go")
    assert llm.run(agent="a", step="s", conversation=conversation,
                   output_type=Answer) == Answer(text="hi")
    payload = fake.payloads[0]
    assert payload["format"] == Answer.model_json_schema()
    assert payload["think"] is False and payload["options"]["num_ctx"] == 32768
    assert payload["messages"][0] == {"role": "system", "content": "sys"}
    assert "JSON Schema" in payload["messages"][-1]["content"]  # schema shown to the model
    assert conversation.messages[-1] == {"role": "assistant", "content": '{"text": "hi"}'}
    assert tracker.calls[0].step == "s/answer" and tracker.calls[0].cost_usd == 0


def test_tools_then_answer():
    llm, fake, tracker = make([
        reply(tool_calls=[call("echo", {"word": "a"}), call("echo", '{"word": "b"}')]),
        reply("done reading"),
        reply('{"text": "final"}'),
    ])
    conversation = Conversation("sys").say("go")
    result = llm.run(agent="a", step="s", conversation=conversation, output_type=Answer,
                     tools=[echo_tool()])
    assert result == Answer(text="final")
    assert "tools" in fake.payloads[0] and "format" not in fake.payloads[0]
    assert "tools" not in fake.payloads[2] and "format" in fake.payloads[2]
    tool_messages = [m for m in fake.payloads[1]["messages"] if m["role"] == "tool"]
    assert [json.loads(m["content"]) for m in tool_messages] == [{"result": "echo: a"},
                                                                {"result": "echo: b"}]
    assert [t.result_ids for t in tracker.tools] == [["P01:t1"], ["P01:t1"]]
    assert [c.step for c in tracker.calls] == ["s", "s/tool-round-1", "s/answer"]


def test_tool_budget_then_answer():
    looping = [reply(tool_calls=[call("echo", {"word": str(i)})]) for i in range(2)]
    llm, fake, _ = make([*looping, reply('{"text": "x"}')], max_tool_rounds=2)
    conversation = Conversation("sys").say("go")
    llm.run(agent="a", step="s", conversation=conversation, output_type=Answer,
            tools=[echo_tool()])
    assert any(isinstance(m, UserTurn) and "Do not call any more tools" in m.text
               for m in conversation.messages)
    assert len(fake.payloads) == 3


def test_invalid_json_gets_one_repair():
    llm, fake, tracker = make([reply('{"wrong": 1}'), reply('{"text": "fixed"}')])
    result = llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                     output_type=Answer)
    assert result == Answer(text="fixed")
    assert "did not match the schema" in fake.payloads[1]["messages"][-1]["content"]
    assert [c.step for c in tracker.calls] == ["s/answer", "s/repair"]

    llm, _, _ = make([reply('{"wrong": 1}'), reply('{"still": "wrong"}')])
    with pytest.raises(LLMError, match="did not match Answer"):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)


def test_length_limits_fail_loudly():
    llm, _, _ = make([reply('{"te', done_reason="length")])
    with pytest.raises(TruncatedError, match="max_tokens"):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"),
                output_type=Answer)
    llm, fake, _ = make([reply('{"text": "x"}')], num_ctx=2048, max_tokens=512)
    with pytest.raises(TruncatedError, match="raise --num-ctx"):
        llm.run(agent="a", step="s", conversation=Conversation("sys").say("x " * 5000),
                output_type=Answer)
    assert fake.payloads == []  # refused before sending


def test_thinking_follows_effort():
    llm, fake, _ = make([reply('{"text": "x"}')], effort="medium")
    llm.run(agent="a", step="s", conversation=Conversation("sys").say("go"), output_type=Answer)
    assert fake.payloads[0]["think"] is True
