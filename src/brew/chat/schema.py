"""SQLite schema for the chat bounded context.

Stores one row per pydantic-ai `ModelMessage` (request or response). Preserves
full fidelity as JSON so threads can be replayed without lossy normalization.
"""

CHAT_SCHEMA: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        thread_id TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN ('request', 'response')),
        payload TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_chat_messages_thread_created
        ON chat_messages(thread_id, created_at)
    """,
]
