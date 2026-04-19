"""Journal domain entities.

A JournalEntry is an immutable record of one completed brew. The `profile_snapshot_at_brew`
blob is a JSON copy of the recipe that was actually used — frozen at brew completion so
later recipe tweaks don't rewrite historical tasting notes.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class JournalEntry:
    id: str
    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    profile_snapshot_at_brew: dict[str, Any]
    water_ml: int
    dose_grams: int
    rating: int | None
    note_text: str | None
    created_at: datetime


@dataclass(frozen=True)
class JournalEntryCreate:
    """Inputs to JournalService.create — used by both the POST /journal route
    (manual log) and the BrewCompleted auto-log subscriber."""

    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    profile_snapshot_at_brew: dict[str, Any]
    water_ml: int
    dose_grams: int


@dataclass(frozen=True)
class JournalEntryUpdate:
    """Partial update — only `rating` and `note_text` are user-editable."""

    rating: int | None = None
    note_text: str | None = None
