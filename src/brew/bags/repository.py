"""Bags repository — Protocol + aiosqlite implementation."""

import json
import uuid
from datetime import date, datetime
from typing import Protocol

import aiosqlite

from brew.bags.model.bag import Bag, BagCreate, BagUpdate
from brew.datetime_utils import now_iso


class BagRepository(Protocol):
    async def create(self, create: BagCreate) -> Bag: ...
    async def get(self, bag_id: str) -> Bag | None: ...
    async def get_active(self) -> Bag | None: ...
    async def list(
        self,
        *,
        active: bool | None = None,
        finished: bool | None = None,
        roaster: str | None = None,
        origin: str | None = None,
    ) -> list[Bag]: ...
    async def update(self, bag_id: str, update: BagUpdate) -> bool: ...
    async def delete(self, bag_id: str) -> bool: ...
    async def activate(self, bag_id: str) -> bool: ...
    async def zero(self, bag_id: str) -> bool: ...
    async def set_remaining_grams(self, bag_id: str, grams: int) -> bool: ...
    async def decrement(self, bag_id: str, grams: int) -> bool: ...


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _parse_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _row_to_bag(row: aiosqlite.Row) -> Bag:
    return Bag(
        id=row["id"],
        name=row["name"],
        origin=row["origin"],
        roaster=row["roaster"],
        roast_date=_parse_date(row["roast_date"]),
        roast_level=row["roast_level"],
        initial_grams=row["initial_grams"],
        remaining_grams=row["remaining_grams"],
        is_active=bool(row["is_active"]),
        opened_at=_parse_datetime(row["opened_at"]),
        finished_at=_parse_datetime(row["finished_at"]) if row["finished_at"] else None,
        profile_id=row["profile_id"],
        profile_snapshot=json.loads(row["profile_snapshot"]),
    )


class BagSqliteRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def create(self, create: BagCreate) -> Bag:
        bag_id = str(uuid.uuid4())
        opened_at = now_iso()
        await self._conn.execute(
            """
            INSERT INTO bags (
                id, name, origin, roaster, roast_date, roast_level,
                initial_grams, remaining_grams, is_active, opened_at,
                finished_at, profile_id, profile_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, NULL, ?, ?)
            """,
            (
                bag_id,
                create.name,
                create.origin,
                create.roaster,
                create.roast_date.isoformat() if create.roast_date else None,
                create.roast_level,
                create.initial_grams,
                create.initial_grams,
                opened_at,
                create.profile_id,
                json.dumps(create.profile_snapshot),
            ),
        )
        await self._conn.commit()
        bag = await self.get(bag_id)
        if bag is None:  # pragma: no cover — INSERT just succeeded
            msg = "Bag disappeared immediately after insert"
            raise RuntimeError(msg)
        return bag

    async def get(self, bag_id: str) -> Bag | None:
        cursor = await self._conn.execute("SELECT * FROM bags WHERE id = ?", (bag_id,))
        row = await cursor.fetchone()
        return _row_to_bag(row) if row else None

    async def get_active(self) -> Bag | None:
        cursor = await self._conn.execute("SELECT * FROM bags WHERE is_active = 1 LIMIT 1")
        row = await cursor.fetchone()
        return _row_to_bag(row) if row else None

    async def list(
        self,
        *,
        active: bool | None = None,
        finished: bool | None = None,
        roaster: str | None = None,
        origin: str | None = None,
    ) -> list[Bag]:
        clauses: list[str] = []
        params: list[object] = []
        if active is not None:
            clauses.append("is_active = ?")
            params.append(1 if active else 0)
        if finished is True:
            clauses.append("finished_at IS NOT NULL")
        elif finished is False:
            clauses.append("finished_at IS NULL")
        if roaster is not None:
            clauses.append("roaster = ?")
            params.append(roaster)
        if origin is not None:
            clauses.append("origin = ?")
            params.append(origin)

        sql = "SELECT * FROM bags"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY opened_at DESC"

        cursor = await self._conn.execute(sql, tuple(params))
        rows = await cursor.fetchall()
        return [_row_to_bag(row) for row in rows]

    async def update(self, bag_id: str, update: BagUpdate) -> bool:
        sets: list[str] = []
        params: list[object] = []
        if update.name is not None:
            sets.append("name = ?")
            params.append(update.name)
        if update.origin is not None:
            sets.append("origin = ?")
            params.append(update.origin)
        if update.roaster is not None:
            sets.append("roaster = ?")
            params.append(update.roaster)
        if update.roast_date is not None:
            sets.append("roast_date = ?")
            params.append(update.roast_date.isoformat())
        if update.roast_level is not None:
            sets.append("roast_level = ?")
            params.append(update.roast_level)
        if update.profile_id is not None:
            sets.append("profile_id = ?")
            params.append(update.profile_id)
        if update.profile_snapshot is not None:
            sets.append("profile_snapshot = ?")
            params.append(json.dumps(update.profile_snapshot))

        if not sets:
            return await self.get(bag_id) is not None

        sql = f"UPDATE bags SET {', '.join(sets)} WHERE id = ?"  # noqa: S608 — no user input in sets
        params.append(bag_id)
        cursor = await self._conn.execute(sql, tuple(params))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def delete(self, bag_id: str) -> bool:
        cursor = await self._conn.execute("DELETE FROM bags WHERE id = ?", (bag_id,))
        await self._conn.commit()
        return cursor.rowcount > 0

    async def activate(self, bag_id: str) -> bool:
        # Optimistic: try to set the target active first. rowcount==0 means it doesn't exist.
        # If it does exist, deactivate any other previously-active bag in the same transaction.
        cursor = await self._conn.execute("UPDATE bags SET is_active = 1 WHERE id = ?", (bag_id,))
        if cursor.rowcount == 0:
            return False
        await self._conn.execute(
            "UPDATE bags SET is_active = 0 WHERE id != ? AND is_active = 1",
            (bag_id,),
        )
        await self._conn.commit()
        return True

    async def zero(self, bag_id: str) -> bool:
        now = now_iso()
        cursor = await self._conn.execute(
            """
            UPDATE bags
            SET remaining_grams = 0, is_active = 0, finished_at = ?
            WHERE id = ?
            """,
            (now, bag_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def set_remaining_grams(self, bag_id: str, grams: int) -> bool:
        clamped = max(0, grams)
        cursor = await self._conn.execute(
            "UPDATE bags SET remaining_grams = ? WHERE id = ?",
            (clamped, bag_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0

    async def decrement(self, bag_id: str, grams: int) -> bool:
        """Atomic decrement; if the result reaches 0, also finish the bag.

        Returns True if a row was matched (bag exists and was not yet finished).
        Returns False on not-found OR already-finished — the caller disambiguates.
        SQL clamps remaining_grams at 0; CASE handles the zero-and-finish in one statement.
        """
        now = now_iso()
        cursor = await self._conn.execute(
            """
            UPDATE bags
            SET remaining_grams = MAX(0, remaining_grams - ?),
                is_active = CASE WHEN remaining_grams - ? <= 0 THEN 0 ELSE is_active END,
                finished_at = CASE WHEN remaining_grams - ? <= 0 THEN ? ELSE finished_at END
            WHERE id = ? AND finished_at IS NULL
            """,
            (grams, grams, grams, now, bag_id),
        )
        await self._conn.commit()
        return cursor.rowcount > 0
