import pytest

from brew.chat.model.event import (
    AgentDone,
    Done,
    Error,
    TextDelta,
    ThinkingDelta,
    ToolCallDelta,
    ToolCallResult,
    ToolCallStart,
)


def test_event_field_shapes() -> None:
    assert TextDelta(text="hi").text == "hi"
    assert ToolCallStart(tool_call_id="c1", tool_name="brew_now").tool_name == "brew_now"
    assert ToolCallDelta(tool_call_id="c1", args_delta="{").args_delta == "{"
    assert ToolCallResult(tool_call_id="c1", result={"ok": True}).result == {"ok": True}
    assert ThinkingDelta(text="...").text == "..."
    assert AgentDone(payload={"role": "model"}).payload == {"role": "model"}
    assert Done(message_id="m1").message_id == "m1"
    assert Error(code="x", message="y").message == "y"


def test_events_are_frozen() -> None:
    ev = TextDelta(text="hi")
    with pytest.raises(AttributeError):
        ev.text = "bye"  # type: ignore[misc]
