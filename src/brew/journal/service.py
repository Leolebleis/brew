"""Journal service — orchestrates the journal repository."""

from datetime import datetime

from brew.errors import NotFoundError
from brew.events.bus import EventBus
from brew.events.domain import JournalEntryCreated
from brew.journal.model.entry import JournalEntry, JournalEntryCreate
from brew.journal.repository import JournalRepository


class JournalService:
    def __init__(self, repo: JournalRepository, bus: EventBus) -> None:
        self._repo = repo
        self._bus = bus

    async def create(self, create: JournalEntryCreate) -> JournalEntry:
        """Insert a journal entry and publish JournalEntryCreated.

        Called by both the BrewCompleted auto-log subscriber and the POST /journal
        route. Publishing is a side effect so every insertion path stays consistent.
        """
        entry = await self._repo.create(create)
        await self._bus.publish(
            JournalEntryCreated(
                entry_id=entry.id,
                brew_started_at=entry.brew_started_at,
                brew_ended_at=entry.brew_ended_at,
                bag_id=entry.bag_id,
                profile_id=entry.profile_id,
                water_ml=entry.water_ml,
                dose_grams=entry.dose_grams,
            )
        )
        return entry

    async def get(self, entry_id: str) -> JournalEntry:
        entry = await self._repo.get(entry_id)
        if entry is None:
            raise NotFoundError(
                message=f"Journal entry {entry_id} not found",
                resource_kind="journal_entry",
                resource_id=entry_id,
            )
        return entry

    async def list(
        self,
        *,
        bag_id: str | None = None,
        profile_id: str | None = None,
        since: datetime | None = None,
        rating_min: int | None = None,
        limit: int = 100,
    ) -> list[JournalEntry]:
        return await self._repo.list(
            bag_id=bag_id,
            profile_id=profile_id,
            since=since,
            rating_min=rating_min,
            limit=limit,
        )

    async def update(self, entry_id: str, *, rating: int | None, note_text: str | None) -> None:
        ok = await self._repo.update(entry_id, rating=rating, note_text=note_text)
        if not ok:
            raise NotFoundError(
                message=f"Journal entry {entry_id} not found",
                resource_kind="journal_entry",
                resource_id=entry_id,
            )

    async def delete(self, entry_id: str) -> None:
        ok = await self._repo.delete(entry_id)
        if not ok:
            raise NotFoundError(
                message=f"Journal entry {entry_id} not found",
                resource_kind="journal_entry",
                resource_id=entry_id,
            )
