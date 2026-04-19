"""Decrement the water reservoir when a journal entry is created.

Subscribes to JournalEntryCreated rather than BrewCompleted so manual logs
(POST /journal) decrement water too.
"""

from collections.abc import Awaitable, Callable

from brew.events.domain import JournalEntryCreated
from brew.water.service import WaterService


def make_water_decrement_handler(
    water_service: WaterService,
) -> Callable[[JournalEntryCreated], Awaitable[None]]:
    async def handle(event: JournalEntryCreated) -> None:
        if event.water_ml <= 0:
            return
        await water_service.decrement(event.water_ml)

    return handle
