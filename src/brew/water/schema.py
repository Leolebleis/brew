"""SQLite schema for the water bounded context.

Single-row table: water_state has id=1 forever. INSERT OR IGNORE seeds the
default 1500 mL on first startup; subsequent runs keep whatever the user has set.
"""

WATER_SCHEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS water_state (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        remaining_ml INTEGER NOT NULL,
        last_refilled_at TEXT NOT NULL
    )
    """,
    """
    INSERT OR IGNORE INTO water_state (id, remaining_ml, last_refilled_at)
    VALUES (1, 1500, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    """,
]
