"""Fan events out to per-connection asyncio queues for SSE streaming.

Usage:
  - `EventBroadcaster` is registered as a subscriber on the `EventBus` in `main.py`.
  - Each SSE connection calls `subscribe()` on app startup and `unsubscribe()` on
    disconnect; the connection reads from its returned `asyncio.Queue`.
  - A bounded queue per subscriber prevents a slow consumer from pinning memory.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

logger = logging.getLogger(__name__)

_QUEUE_MAX = 32


class EventBroadcaster:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=_QUEUE_MAX)
        self._queues.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with contextlib.suppress(ValueError):
            self._queues.remove(queue)

    async def broadcast(self, event: object) -> None:
        for queue in list(self._queues):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(
                    "dropping SSE event — subscriber queue full",
                    extra={"event_type": type(event).__name__},
                )
