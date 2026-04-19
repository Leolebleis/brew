"""Decrement the journaled bag when a journal entry is created.

Subscribes to JournalEntryCreated rather than BrewCompleted so manual logs
(POST /journal) decrement the bag too.
"""

from collections.abc import Awaitable, Callable

from brew.bags.service import BagService
from brew.errors import NotFoundError
from brew.events.domain import JournalEntryCreated


def make_bag_decrement_handler(
    bag_service: BagService,
) -> Callable[[JournalEntryCreated], Awaitable[None]]:
    async def handle(event: JournalEntryCreated) -> None:
        if event.bag_id is None or event.dose_grams <= 0:
            return
        try:
            await bag_service.decrement(event.bag_id, event.dose_grams)
        except NotFoundError:
            # Bag was deleted between journal insert and subscriber dispatch — skip.
            return

    return handle
