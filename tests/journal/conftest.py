from datetime import UTC, datetime
from typing import Any

from brew.journal.model.entry import JournalEntry, JournalEntryCreate


def make_entry(**overrides: Any) -> JournalEntry:
    defaults: dict[str, Any] = {
        "id": "entry-1",
        "brew_started_at": datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC),
        "brew_ended_at": datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
        "bag_id": "bag-1",
        "profile_id": "profile-1",
        "profile_snapshot_at_brew": {"ratio": 60.0, "bloom_duration": 30},
        "water_ml": 500,
        "dose_grams": 30,
        "rating": None,
        "note_text": None,
        "created_at": datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return JournalEntry(**defaults)


def make_entry_create(**overrides: Any) -> JournalEntryCreate:
    defaults: dict[str, Any] = {
        "brew_started_at": datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC),
        "brew_ended_at": datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
        "bag_id": "bag-1",
        "profile_id": "profile-1",
        "profile_snapshot_at_brew": {"ratio": 60.0, "bloom_duration": 30},
        "water_ml": 500,
        "dose_grams": 30,
    }
    defaults.update(overrides)
    return JournalEntryCreate(**defaults)
