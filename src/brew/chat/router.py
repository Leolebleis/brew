"""Chat HTTP router — POST /chat/messages (SSE), GET /chat/messages (JSON)."""

import json
import re
from collections.abc import AsyncGenerator
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from brew.chat.dependencies import get_chat_service
from brew.chat.mapper import ChatMessageMapper
from brew.chat.model.api import ChatGetResponse, ChatPostRequest
from brew.chat.service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])

_DEFAULT_THREAD_ID = "default"
_CAMEL_TO_SNAKE = re.compile(r"(?<!^)(?=[A-Z])")


def _event_to_sse(event: object) -> ServerSentEvent:
    """Map a ChatStreamEvent dataclass to its SSE wire representation.

    Wire event name is the snake_case'd class name; data is the dataclass
    fields verbatim. The chat event dataclasses are designed so their field
    names already match the wire shape.
    """
    name = _CAMEL_TO_SNAKE.sub("_", type(event).__name__).lower()
    return ServerSentEvent(event=name, data=json.dumps(asdict(event)))  # ty: ignore[invalid-argument-type]


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
        messages=[ChatMessageMapper.to_api_response(m) for m in messages],
        next_before_id=next_before_id,
    )
