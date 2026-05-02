"""Mapper unit tests — fabricates pydantic-ai event instances directly."""

from pydantic_ai.messages import (
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)

from brew.chat.mapper import pydantic_ai_to_agent_event
from brew.chat.model.event import (
    TextDelta,
    ThinkingDelta,
    ToolCallDelta,
)


def test_part_delta_text() -> None:
    ev = PartDeltaEvent(index=0, delta=TextPartDelta(content_delta="hello"))
    out = pydantic_ai_to_agent_event(ev)
    assert out == TextDelta(text="hello")


def test_part_delta_thinking() -> None:
    ev = PartDeltaEvent(index=0, delta=ThinkingPartDelta(content_delta="reasoning..."))
    out = pydantic_ai_to_agent_event(ev)
    assert out == ThinkingDelta(text="reasoning...")


def test_part_delta_tool_call_args_streaming() -> None:
    ev = PartDeltaEvent(
        index=0,
        delta=ToolCallPartDelta(tool_call_id="c1", args_delta='{"profile_id": "x"}'),
    )
    out = pydantic_ai_to_agent_event(ev)
    assert out == ToolCallDelta(tool_call_id="c1", args_delta='{"profile_id": "x"}')


def test_part_start_event_is_dropped() -> None:
    ev = PartStartEvent(index=0, part=TextPart(content="hi"))
    out = pydantic_ai_to_agent_event(ev)
    assert out is None


def test_unknown_event_returns_none() -> None:
    out = pydantic_ai_to_agent_event(object())
    assert out is None


def test_tool_call_part_delta_with_empty_args() -> None:
    ev = PartDeltaEvent(index=0, delta=ToolCallPartDelta(tool_call_id="c1", args_delta=None))
    out = pydantic_ai_to_agent_event(ev)
    assert out == ToolCallDelta(tool_call_id="c1", args_delta="")
