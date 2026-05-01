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
    async def list_thread(self, thread_id: str) -> list[ChatMessage]: ...
    async def list_threads(self) -> list[str]: ...


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

    async def list_thread(self, thread_id: str) -> list[ChatMessage]:
        # rowid tiebreaker keeps insertion order stable when two rows share a created_at.
        cursor = await self._conn.execute(
            "SELECT * FROM chat_messages WHERE thread_id = ? ORDER BY created_at ASC, rowid ASC",
            (thread_id,),
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
