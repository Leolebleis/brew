"""Auto-log a journal entry when the poller detects a completed brew.

Converts BrewCompleted → JournalService.create, which publishes JournalEntryCreated
for downstream consumers (water/bag decrement, SSE broadcaster).
"""

from collections.abc import Awaitable, Callable

from brew.bags.service import BagService
from brew.events.domain import BrewCompleted
from brew.journal.defaults import derive_brew_metrics
from brew.journal.model.entry import JournalEntryCreate
from brew.journal.service import JournalService


def make_journal_auto_log_handler(
    journal_service: JournalService,
    bag_service: BagService,
) -> Callable[[BrewCompleted], Awaitable[None]]:
    async def handle(event: BrewCompleted) -> None:
        bag = await bag_service.get_active()
        matches = bag is not None and bag.profile_id == event.profile_id
        snapshot = bag.profile_snapshot if (bag and matches) else {}
        water_ml, dose_grams = derive_brew_metrics(snapshot)

        await journal_service.create(
            JournalEntryCreate(
                brew_started_at=event.brew_started_at,
                brew_ended_at=event.brew_ended_at,
                bag_id=bag.id if (bag and matches) else None,
                profile_id=event.profile_id,
                profile_snapshot_at_brew=dict(snapshot),
                water_ml=water_ml,
                dose_grams=dose_grams,
            )
        )

    return handle
