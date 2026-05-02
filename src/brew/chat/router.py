"""Chat HTTP router — POST /chat/messages (SSE), GET /chat/messages (JSON)."""

import json
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from brew.chat.dependencies import get_chat_service
from brew.chat.mapper import chat_message_to_response
from brew.chat.model.api import ChatGetResponse, ChatPostRequest
from brew.chat.model.event import (
    Done,
    Error,
    TextDelta,
    ThinkingDelta,
    ToolCallDelta,
    ToolCallResult,
    ToolCallStart,
)
from brew.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

_DEFAULT_THREAD_ID = "default"


def _event_to_sse(event: object) -> ServerSentEvent:  # noqa: PLR0911
    """Map a ChatStreamEvent to its wire SSE representation."""
    match event:
        case TextDelta(text=text):
            return ServerSentEvent(event="text_delta", data=json.dumps({"text": text}))
        case ToolCallStart(tool_call_id=cid, tool_name=name):
            return ServerSentEvent(
                event="tool_call_start",
                data=json.dumps({"tool_call_id": cid, "tool_name": name}),
            )
        case ToolCallDelta(tool_call_id=cid, args_delta=delta):
            return ServerSentEvent(
                event="tool_call_delta",
                data=json.dumps({"tool_call_id": cid, "args_delta": delta}),
            )
        case ToolCallResult(tool_call_id=cid, result=result):
            return ServerSentEvent(
                event="tool_call_result",
                data=json.dumps({"tool_call_id": cid, "result": result}),
            )
        case ThinkingDelta(text=text):
            return ServerSentEvent(event="thinking_delta", data=json.dumps({"text": text}))
        case Done(message_id=mid):
            return ServerSentEvent(event="done", data=json.dumps({"message_id": mid}))
        case Error(code=code, message=msg):
            return ServerSentEvent(event="error", data=json.dumps({"code": code, "message": msg}))
        case _:
            msg = f"Unknown ChatStreamEvent type: {type(event).__name__}"
            raise TypeError(msg)


@router.post("/messages")
async def post_message(
    request: ChatPostRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> EventSourceResponse:
    async def generator() -> AsyncGenerator[ServerSentEvent]:
        async for ev in service.stream_message(_DEFAULT_THREAD_ID, request.text):
            yield _event_to_sse(ev)

    return EventSourceResponse(generator())


@router.get("/messages")
async def get_messages(
    service: Annotated[ChatService, Depends(get_chat_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before_id: Annotated[str | None, Query()] = None,
) -> ChatGetResponse:
    messages, next_before_id = await service.get_thread(_DEFAULT_THREAD_ID, limit=limit, before_id=before_id)
    return ChatGetResponse(
        messages=[chat_message_to_response(m) for m in messages],
        next_before_id=next_before_id,
    )
