"""SQLite schema for the bags bounded context.

Durable bean-history log. A bag is the local sidecar for a Fellow profile:
`profile_id` points at the Fellow profile if it still exists; `profile_snapshot`
is the authoritative local copy of recipe params so recipes survive Fellow
profile deletion (Fellow caps profile slots).

Invariants:
- At most one row has `is_active = 1` (enforced by `BagSqliteRepository.activate`).
- `remaining_grams` clamped >= 0 on write.
- `finished_at IS NOT NULL` implies `remaining_grams = 0` and `is_active = 0`.
"""

BAGS_SCHEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS bags (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        origin TEXT NOT NULL,
        roaster TEXT NOT NULL,
        roast_date TEXT,
        roast_level TEXT NOT NULL,
        initial_grams INTEGER NOT NULL,
        remaining_grams INTEGER NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 0,
        opened_at TEXT NOT NULL,
        finished_at TEXT,
        profile_id TEXT,
        profile_snapshot TEXT NOT NULL
    )
    """,
]
