"""Cost and latency tracking per run: every model call and tool call is recorded."""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field

from discovery_chef.llm.pricing import TokenUsage

TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens", "thinking_tokens")


@dataclass
class CallRecord:
    agent: str
    step: str  # e.g. "draft", "revision-1", "synthesis/tool-round-3"
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    thinking_tokens: int
    cost_usd: float | None
    latency_s: float
    finish_reason: str | None
    model_version: str | None = None


@dataclass
class ToolRecord:
    agent: str
    tool: str
    input: dict
    result_ids: list[str]
    is_error: bool = False


@dataclass
class RunTracker:
    calls: list[CallRecord] = field(default_factory=list)
    tools: list[ToolRecord] = field(default_factory=list)
    started: float = field(default_factory=time.perf_counter)
    finished: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_call(self, *, agent: str, step: str, usage: TokenUsage, latency_s: float,
                 finish_reason: str | None, model_version: str | None = None) -> None:
        cost = usage.cost_usd
        record = CallRecord(
            agent=agent, step=step, model=usage.model,
            **{name: getattr(usage, name) for name in TOKEN_FIELDS},
            cost_usd=None if cost is None else round(cost, 6),
            latency_s=round(latency_s, 3), finish_reason=finish_reason,
            model_version=model_version,
        )
        with self._lock:  # the two analysts record from parallel threads
            self.calls.append(record)

    def add_tool(self, record: ToolRecord) -> None:
        with self._lock:
            self.tools.append(record)

    def finish(self) -> None:
        self.finished = time.perf_counter()

    @property
    def wall_clock_s(self) -> float:
        end = self.finished if self.finished is not None else time.perf_counter()
        return round(end - self.started, 3)

    def summary(self) -> dict:
        per_agent: dict[str, dict] = defaultdict(lambda: {
            "calls": 0, **dict.fromkeys(TOKEN_FIELDS, 0), "cost_usd": 0.0, "latency_s": 0.0,
            "tool_calls": 0,
        })
        unknown_cost = False
        for call in self.calls:
            agg = per_agent[call.agent]
            agg["calls"] += 1
            for name in TOKEN_FIELDS:
                agg[name] += getattr(call, name)
            if call.cost_usd is None:
                unknown_cost = True
            else:
                agg["cost_usd"] += call.cost_usd
            agg["latency_s"] += call.latency_s
        for tool in self.tools:
            per_agent[tool.agent]["tool_calls"] += 1
        for agg in per_agent.values():
            agg["cost_usd"] = round(agg["cost_usd"], 6)
            agg["latency_s"] = round(agg["latency_s"], 3)

        totals = {key: sum(a[key] for a in per_agent.values())
                  for key in ("calls", *TOKEN_FIELDS, "tool_calls")}
        totals["cost_usd"] = round(sum(a["cost_usd"] for a in per_agent.values()), 6)
        totals["model_time_s"] = round(sum(a["latency_s"] for a in per_agent.values()), 3)
        totals["wall_clock_s"] = self.wall_clock_s
        totals["cost_incomplete"] = unknown_cost
        return {
            "totals": totals,
            "per_agent": dict(per_agent),
            "calls": [asdict(c) for c in self.calls],
            "tool_calls": [asdict(t) for t in self.tools],
        }
