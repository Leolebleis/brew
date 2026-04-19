"""In-process async event bus.

Handlers for an event type fire concurrently on `publish`. A handler that raises
is logged and swallowed — one broken subscriber must not sink the others.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

Event = TypeVar("Event")
Handler = Callable[[Event], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: type[Event], handler: Handler[Event]) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: object) -> None:
        handlers = self._handlers.get(type(event), [])
        if not handlers:
            return
        results = await asyncio.gather(
            *(handler(event) for handler in handlers),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.exception(
                    "event handler raised",
                    exc_info=result,
                    extra={"event_type": type(event).__name__},
                )
