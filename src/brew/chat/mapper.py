"""Chat mappers — pydantic-ai event union → AgentStreamEvent; ChatMessage → API response.

The pydantic-ai event mapper is pure; tests fabricate event instances
directly without invoking a model.
"""

import logging
from typing import Any

from pydantic import ValidationError
from pydantic_ai import AgentRunResultEvent
from pydantic_ai.messages import (
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessagesTypeAdapter,
    PartDeltaEvent,
    PartStartEvent,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)

from brew.chat.model.api import ChatMessageResponse
from brew.chat.model.event import (
    AgentDone,
    AgentStreamEvent,
    TextDelta,
    ThinkingDelta,
    ToolCallDelta,
    ToolCallResult,
    ToolCallStart,
)
from brew.chat.model.message import ChatMessage
from brew.chat.projections import project_message

logger = logging.getLogger(__name__)


def pydantic_ai_to_agent_event(event: Any) -> AgentStreamEvent | None:  # noqa: ANN401, PLR0911
    """Map a pydantic-ai stream event to our internal AgentStreamEvent.

    Returns None for events we deliberately drop (`PartStartEvent`,
    `FinalResultEvent`).
    """
    if isinstance(event, PartDeltaEvent):
        delta = event.delta
        if isinstance(delta, TextPartDelta):
            return TextDelta(text=delta.content_delta)
        if isinstance(delta, ThinkingPartDelta):
            return ThinkingDelta(text=delta.content_delta or "")
        if isinstance(delta, ToolCallPartDelta):
            return ToolCallDelta(
                tool_call_id=delta.tool_call_id or "",
                args_delta=delta.args_delta or "",
            )
        return None

    if isinstance(event, FunctionToolCallEvent):
        return ToolCallStart(
            tool_call_id=event.part.tool_call_id,
            tool_name=event.part.tool_name,
        )

    if isinstance(event, FunctionToolResultEvent):
        return ToolCallResult(
            tool_call_id=event.result.tool_call_id,
            result=event.result.content,
        )

    if isinstance(event, AgentRunResultEvent):
        # Persist the response ModelMessage (last entry in result.new_messages()).
        response_msg = event.result.new_messages()[-1]
        payload = ModelMessagesTypeAdapter.dump_python([response_msg], mode="json")[0]
        return AgentDone(payload=payload)

    # Drop: PartStartEvent (non-actionable), FinalResultEvent (informational only).
    if isinstance(event, PartStartEvent | FinalResultEvent):
        return None

    return None


class ChatMessageMapper:
    @staticmethod
    def to_api_response(msg: ChatMessage) -> ChatMessageResponse:
        # Deserialize the raw payload into ModelMessage(s) and project the first
        # one — chat_messages stores one ModelMessage per row.
        try:
            messages = ModelMessagesTypeAdapter.validate_python([msg.payload])
            projected = project_message(messages[0]) if messages else None
        except (ValidationError, ValueError) as exc:
            # Stored payload doesn't match the current pydantic-ai schema —
            # log so we notice shape drift, but stay best-effort for callers.
            logger.warning("chat projection failed for message %s: %s", msg.id, exc)
            projected = None
        return ChatMessageResponse(
            id=msg.id,
            kind=msg.kind,
            payload=msg.payload,
            projected=projected,
            created_at=msg.created_at,
        )
