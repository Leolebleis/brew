"""Chat streaming event unions.

`AgentStreamEvent` is yielded by the ChatAgent Protocol — its terminal is
`AgentDone(payload)`, carrying the raw ModelMessage JSON for the service
to persist.

`ChatStreamEvent` is yielded by ChatService.stream_message and encoded
1:1 onto the SSE wire — its terminal is `Done(message_id)` after
persistence; `Error` for failure mid-stream.

The service translates between them: shared events pass through unchanged,
`AgentDone` triggers persistence and is replaced by `Done(message_id)`.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TextDelta:
    text: str


@dataclass(frozen=True)
class ToolCallStart:
    tool_call_id: str
    tool_name: str


@dataclass(frozen=True)
class ToolCallDelta:
    tool_call_id: str
    args_delta: str


@dataclass(frozen=True)
class ToolCallResult:
    tool_call_id: str
    result: Any  # JSON-serializable: dict / str / list / None — preserved as-is on the wire


@dataclass(frozen=True)
class ThinkingDelta:
    text: str


@dataclass(frozen=True)
class AgentDone:
    """Terminal event from ChatAgent.stream — carries the response payload for the service to persist."""

    payload: dict[str, Any]


@dataclass(frozen=True)
class Done:
    """Terminal event on the wire — carries the persisted assistant-row id."""

    message_id: str


@dataclass(frozen=True)
class Error:
    code: str
    message: str


# Yielded by ChatAgent.stream
AgentStreamEvent = TextDelta | ToolCallStart | ToolCallDelta | ToolCallResult | ThinkingDelta | AgentDone | Error

# Yielded by ChatService.stream_message (wire-side, after persistence translation)
ChatStreamEvent = TextDelta | ToolCallStart | ToolCallDelta | ToolCallResult | ThinkingDelta | Done | Error
