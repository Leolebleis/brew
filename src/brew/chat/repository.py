"""Chat repository — Protocol + aiosqlite implementation."""

import json
import uuid
from datetime import UTC, datetime
from typing import Protocol

import aiosqlite

from brew.chat.model.message import ChatMessage, ChatMessageCreate
from brew.datetime_utils import from_iso, to_iso


class ChatRepository(Protocol):
    async def append(self, create: ChatMessageCreate) -> ChatMessage: ...
    async def get_message(self, message_id: str) -> ChatMessage | None: ...
    async def list_thread(
        self,
        thread_id: str,
        *,
        limit: int = 50,
        before: tuple[str, int] | None = None,
    ) -> list[ChatMessage]: ...
    async def list_threads(self) -> list[str]: ...
    async def load_history(self, thread_id: str, *, max_messages: int = 200) -> list[ChatMessage]: ...


def _row_to_chat_message(row: aiosqlite.Row) -> ChatMessage:
    return ChatMessage(
        id=row["id"],
        thread_id=row["thread_id"],
        kind=row["kind"],
        payload=json.loads(row["payload"]),
        created_at=from_iso(row["created_at"]),
    )


class ChatSqliteRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def append(self, create: ChatMessageCreate) -> ChatMessage:
        message_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)
        await self._conn.execute(
            """
            INSERT INTO chat_messages (id, thread_id, kind, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, create.thread_id, create.kind, json.dumps(create.payload), to_iso(created_at)),
        )
        await self._conn.commit()
        return ChatMessage(
            id=message_id,
            thread_id=create.thread_id,
            kind=create.kind,
            payload=create.payload,
            created_at=created_at,
        )

    async def get_message(self, message_id: str) -> ChatMessage | None:
        cursor = await self._conn.execute(
            "SELECT * FROM chat_messages WHERE id = ?",
            (message_id,),
        )
        row = await cursor.fetchone()
        return _row_to_chat_message(row) if row else None

    async def list_thread(
        self,
        thread_id: str,
        *,
        limit: int = 50,
        before: tuple[str, int] | None = None,
    ) -> list[ChatMessage]:
        """Newest-first, paginated. `before=(created_at_iso, rowid)` returns rows strictly older."""
        if before is None:
            cursor = await self._conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE thread_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (thread_id, limit),
            )
        else:
            before_created_at, before_rowid = before
            cursor = await self._conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE thread_id = ?
                  AND (created_at, rowid) < (?, ?)
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (thread_id, before_created_at, before_rowid, limit),
            )
        rows = await cursor.fetchall()
        return [_row_to_chat_message(row) for row in rows]

    async def list_threads(self) -> list[str]:
        # MAX(rowid) tiebreaks threads whose latest message shares a created_at.
        cursor = await self._conn.execute(
            """
            SELECT thread_id, MAX(created_at) AS latest, MAX(rowid) AS last_rowid
            FROM chat_messages
            GROUP BY thread_id
            ORDER BY latest DESC, last_rowid DESC
            """
        )
        rows = await cursor.fetchall()
        return [row["thread_id"] for row in rows]

    async def load_history(self, thread_id: str, *, max_messages: int = 200) -> list[ChatMessage]:
        """Oldest-first, capped — for feeding pydantic-ai message_history.

        If a thread has more than `max_messages` rows, the most recent
        `max_messages` are kept (window slides as conversations grow).
        """
        cursor = await self._conn.execute(
            """
            SELECT * FROM chat_messages
            WHERE thread_id = ?
            ORDER BY created_at DESC, rowid DESC
            LIMIT ?
            """,
            (thread_id, max_messages),
        )
        rows = await cursor.fetchall()
        # Reverse to oldest-first (pydantic-ai expects chronological order).
        return list(reversed([_row_to_chat_message(row) for row in rows]))
