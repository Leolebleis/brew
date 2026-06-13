"""Journal repository — Protocol + aiosqlite implementation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import builtins

    import aiosqlite

from brew.datetime_utils import now_iso, to_iso
from brew.journal.model.entry import JournalEntry, JournalEntryCreate, TastingAxes


class JournalRepository(Protocol):
    async def create(self, create: JournalEntryCreate) -> JournalEntry: ...
    async def get(self, entry_id: str) -> JournalEntry | None: ...
    async def list(
        self,
        *,
        bag_id: str | None = None,
        profile_id: str | None = None,
        since: datetime | None = None,
        rating_min: int | None = None,
        limit: int = 100,
    ) -> builtins.list[JournalEntry]: ...
    async def update(self, entry_id: str, *, rating: int | None, note_text: str | None) -> bool: ...
    async def delete(self, entry_id: str) -> bool: ...
    async def record_tasting(  # noqa: PLR0913
        self,
        entry_id: str,
        *,
        axes: TastingAxes | None = None,
        flavor_tags: builtins.list[str] | None = None,
        note_text: str | None = None,
        rating: int | None = None,
        bean_dimensions_snapshot: dict | None = None,
    ) -> bool: ...


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _row_to_entry(row: aiosqlite.Row) -> JournalEntry:
    return JournalEntry(
        id=row["id"],
        brew_started_at=_parse_datetime(row["brew_started_at"]),
        brew_ended_at=_parse_datetime(row["brew_ended_at"]),
        bag_id=row["bag_id"],
        profile_id=row["profile_id"],
        profile_snapshot_at_brew=json.loads(row["profile_snapshot_at_brew"]),
        water_ml=row["water_ml"],
        dose_grams=row["dose_grams"],
        rating=row["rating"],
        note_text=row["note_text"],
        created_at=_parse_datetime(row["created_at"]),
        acidity=row["acidity"],
        bitterness=row["bitterness"],
        body=row["body"],
        sweetness=row["sweetness"],
        strength=row["strength"],
        flavor_tags=json.loads(row["flavor_tags"]),
        bean_dimensions_snapshot=(
            json.loads(row["bean_dimensions_snapshot"]) if row["bean_dimensions_snapshot"] else None
        ),
    )


class JournalSqliteRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, create: JournalEntryCreate) -> JournalEntry:
        entry_id = str(uuid.uuid4())
        created_at = now_iso()
        await self._conn.execute(
            """
            INSERT INTO journal_entries (
                id, brew_started_at, brew_ended_at, bag_id, profile_id,
                profile_snapshot_at_brew, water_ml, dose_grams, rating, note_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
            """,
            (
                entry_id,
                to_iso(create.brew_started_at),
                to_iso(create.brew_ended_at),
                create.bag_id,
                create.profile_id,
                json.dumps(create.profile_snapshot_at_brew),
                create.water_ml,
                create.dose_grams,
                created_at,
            ),
        )
        await self._conn.commit()
        entry = await self.get(entry_id)
        if entry is None:  # pragma: no cover — INSERT just succeeded
            msg = "JournalEntry disappeared immediately after insert"
            raise RuntimeError(msg)
        return entry

    async def get(self, entry_id: str) -> JournalEntry | None:
        cursor = await self._conn.execute("SELECT * FROM journal_entries WHERE id = ?", (entry_id,))
        row = await cursor.fetchone()
        return _row_to_entry(row) if row else None

    async def list(
        self,
        *,
        bag_id: str | None = None,
        profile_id: str | None = None,
        since: datetime | None = None,
        rating_min: int | None = None,
        limit: int = 100,
    ) -> builtins.list[JournalEntry]:
        clauses: list[str] = []
        params: list[object] = []
        if bag_id is not None:
            clauses.append("bag_id = ?")
            params.append(bag_id)
        if profile_id is not None:
            clauses.append("profile_id = ?")
            params.append(profile_id)
        if since is not None:
            clauses.append("brew_ended_at >= ?")
            params.append(to_iso(since))
        if rating_min is not None:
            clauses.append("rating >= ?")
            params.append(rating_min)

        sql = "SELECT * FROM journal_entries"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY brew_ended_at DESC LIMIT ?"
        params.append(limit)

        cursor = await self._conn.execute(sql, tuple(params))
        rows = await cursor.fetchall()
        return [_row_to_entry(row) for row in rows]

    async def update(self, entry_id: str, *, rating: int | None, note_text: str | None) -> bool:
        sets: list[str] = []
        params: list[object] = []
        if rating is not None:
            sets.append("rating = ?")
            params.append(rating)
        if note_text is not None:
            sets.append("note_text = ?")
            params.append(note_text)

        if not sets:
            return await self.get(entry_id) is not None

        sql = f"UPDATE journal_entries SET {', '.join(sets)} WHERE id = ?"  # noqa: S608
        params.append(entry_id)
        cursor = await self._conn.execute(sql, tuple(params))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def record_tasting(  # noqa: PLR0913
        self,
        entry_id: str,
        *,
        axes: TastingAxes | None = None,
        flavor_tags: builtins.list[str] | None = None,
        note_text: str | None = None,
        rating: int | None = None,
        bean_dimensions_snapshot: dict | None = None,
    ) -> bool:
        sets: list[str] = []
        params: list[object] = []
        if axes is not None:
            for name in ("acidity", "bitterness", "body", "sweetness", "strength"):
                value = getattr(axes, name)
                if value is not None:
                    sets.append(f"{name} = ?")
                    params.append(value)
        if flavor_tags is not None:
            sets.append("flavor_tags = ?")
            params.append(json.dumps(flavor_tags))
        if note_text is not None:
            sets.append("note_text = ?")
            params.append(note_text)
        if rating is not None:
            sets.append("rating = ?")
            params.append(rating)
        if bean_dimensions_snapshot is not None:
            sets.append("bean_dimensions_snapshot = ?")
            params.append(json.dumps(bean_dimensions_snapshot))

        if not sets:
            return await self.get(entry_id) is not None

        sql = f"UPDATE journal_entries SET {', '.join(sets)} WHERE id = ?"  # noqa: S608
        params.append(entry_id)
        cursor = await self._conn.execute(sql, tuple(params))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def delete(self, entry_id: str) -> bool:
        cursor = await self._conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
        await self._conn.commit()
        return cursor.rowcount > 0
