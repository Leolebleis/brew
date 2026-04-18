"""Bags repository — Protocol + aiosqlite implementation."""

import json
import uuid
from datetime import UTC, date, datetime
from typing import Protocol

import aiosqlite

from brew.bags.model.bag import Bag, BagCreate


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


def _now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


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
        opened_at = _now_iso()
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
