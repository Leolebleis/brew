"""SQLite schema for the journal bounded context.

One row per completed brew. Created via `JournalService.create` — from the
`POST /journal` route (manual log) or the `BrewCompleted` auto-log subscriber.

Invariants:
- `profile_snapshot_at_brew` is frozen at brew time; never updated.
- `bag_id` and `profile_id` are nullable FKs that survive deletion of the referenced rows.
- `rating` is NULL until the user rates the brew; allowed values when set are 1..5.
"""

JOURNAL_SCHEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS journal_entries (
        id TEXT PRIMARY KEY,
        brew_started_at TEXT NOT NULL,
        brew_ended_at TEXT NOT NULL,
        bag_id TEXT,
        profile_id TEXT,
        profile_snapshot_at_brew TEXT NOT NULL,
        water_ml INTEGER NOT NULL,
        dose_grams INTEGER NOT NULL,
        rating INTEGER CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
        note_text TEXT,
        created_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_journal_brew_ended_at ON journal_entries(brew_ended_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_journal_bag_id ON journal_entries(bag_id)",
    "CREATE INDEX IF NOT EXISTS idx_journal_profile_id ON journal_entries(profile_id)",
]
