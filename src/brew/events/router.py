import asyncio
import json
from collections.abc import AsyncGenerator
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from brew.events.broadcaster import EventBroadcaster
from brew.events.dependencies import get_event_broadcaster

router = APIRouter(tags=["events"])


@router.get("/events")
async def events_stream(
    request: Request,
    broadcaster: Annotated[EventBroadcaster, Depends(get_event_broadcaster)],
) -> EventSourceResponse:
    queue = broadcaster.subscribe()

    async def event_generator() -> AsyncGenerator[ServerSentEvent]:
        try:
            while True:
                if await request.is_disconnected():
                    return
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except TimeoutError:
                    yield ServerSentEvent(comment="keepalive")
                    continue
                yield ServerSentEvent(
                    event=type(event).__name__,
                    data=json.dumps(asdict(event), default=str),
                )
        finally:
            broadcaster.unsubscribe(queue)

    return EventSourceResponse(event_generator())
