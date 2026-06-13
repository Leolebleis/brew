"""Journal domain entities.

A JournalEntry is an immutable record of one completed brew. The `profile_snapshot_at_brew`
blob is a JSON copy of the recipe that was actually used — frozen at brew completion so
later recipe tweaks don't rewrite historical tasting notes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TastingAxes:
    """Signed -2..+2 tasting axes (0 = balanced). All optional until rated."""

    acidity: int | None = None
    bitterness: int | None = None
    body: int | None = None
    sweetness: int | None = None
    strength: int | None = None


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
    acidity: int | None = None
    bitterness: int | None = None
    body: int | None = None
    sweetness: int | None = None
    strength: int | None = None
    flavor_tags: list[str] = field(default_factory=list)
    bean_dimensions_snapshot: dict[str, Any] | None = None


@dataclass(frozen=True)
class JournalEntryCreate:
    """Inputs to JournalService.create."""

    brew_started_at: datetime
    brew_ended_at: datetime
    bag_id: str | None
    profile_id: str | None
    profile_snapshot_at_brew: dict[str, Any]
    water_ml: int
    dose_grams: int
