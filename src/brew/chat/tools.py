"""Agent-local tools — chat-only, NOT exposed via MCP.

These are specific to the chat agent's read patterns. The /brew skill uses MCP
resources directly (coffee://journal, coffee://bags); the chat agent needs
filtered, semantic queries that match its turn-by-turn reasoning."""

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Annotated

from pydantic import Field

from brew.bags.service import BagService
from brew.journal.service import JournalService


def make_query_journal(journal_service: JournalService) -> Callable[..., Awaitable[list[dict]]]:
    async def query_journal(
        bag_id: Annotated[str | None, Field(description="Filter to one bag.")] = None,
        profile_id: Annotated[str | None, Field(description="Filter to one Fellow profile.")] = None,
        since: Annotated[datetime | None, Field(description="ISO timestamp; only entries after this.")] = None,
        rating_min: Annotated[int | None, Field(ge=1, le=5, description="Minimum star rating.")] = None,
        limit: Annotated[int, Field(ge=1, le=50, description="Max entries to return.")] = 10,
    ) -> list[dict]:
        """Read brew journal entries with filters. Use to look up tasting history."""
        entries = await journal_service.list(
            bag_id=bag_id,
            profile_id=profile_id,
            since=since,
            rating_min=rating_min,
            limit=limit,
        )
        return [
            {
                "id": e.id,
                "brew_ended_at": e.brew_ended_at.isoformat(),
                "bag_id": e.bag_id,
                "profile_id": e.profile_id,
                "water_ml": e.water_ml,
                "dose_grams": e.dose_grams,
                "rating": e.rating,
                "note_text": e.note_text,
            }
            for e in entries
        ]

    return query_journal


def make_find_historical_bag(bag_service: BagService) -> Callable[..., Awaitable[list[dict]]]:
    async def find_historical_bag(
        roaster: Annotated[str | None, Field(description="Match exact roaster.")] = None,
        origin: Annotated[str | None, Field(description="Match exact origin.")] = None,
        name: Annotated[str | None, Field(description="Match exact bag name.")] = None,
    ) -> list[dict]:
        """Find past bags by roaster/origin/name. Use when user mentions a bean
        they may have had before — the bag's profile_snapshot lets you 'resurrect'
        the recipe."""
        bags = await bag_service.list(roaster=roaster, origin=origin)
        if name is not None:
            bags = [b for b in bags if b.name == name]
        return [
            {
                "id": b.id,
                "name": b.name,
                "origin": b.origin,
                "roaster": b.roaster,
                "roast_date": b.roast_date.isoformat() if b.roast_date else None,
                "is_active": b.is_active,
                "finished_at": b.finished_at.isoformat() if b.finished_at else None,
                "profile_snapshot": b.profile_snapshot,
            }
            for b in bags
        ]

    return find_historical_bag
