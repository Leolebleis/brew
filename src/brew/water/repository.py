"""Water repository — Protocol + aiosqlite implementation."""

from datetime import datetime
from typing import Protocol

import aiosqlite

from brew.datetime_utils import now_iso
from brew.water.model.water import Water

_MAX_ML = 1500


class WaterRepository(Protocol):
    async def get(self) -> Water: ...
    async def set_remaining_ml(self, ml: int) -> None: ...
    async def decrement(self, ml: int) -> None: ...
    async def refill(self) -> None: ...


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


class WaterSqliteRepository:
    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn

    async def get(self) -> Water:
        cursor = await self._conn.execute("SELECT remaining_ml, last_refilled_at FROM water_state WHERE id = 1")
        row = await cursor.fetchone()
        if row is None:  # pragma: no cover — seeded by INSERT OR IGNORE in schema
            msg = "water_state row missing — schema seed did not run"
            raise RuntimeError(msg)
        return Water(
            remaining_ml=row["remaining_ml"],
            last_refilled_at=_parse_iso(row["last_refilled_at"]),
        )

    async def set_remaining_ml(self, ml: int) -> None:
        clamped = max(0, min(ml, _MAX_ML))
        await self._conn.execute(
            "UPDATE water_state SET remaining_ml = ? WHERE id = 1",
            (clamped,),
        )
        await self._conn.commit()

    async def decrement(self, ml: int) -> None:
        # Single statement avoids the read-then-write roundtrip; SQLite clamps to [0, _MAX_ML].
        await self._conn.execute(
            "UPDATE water_state SET remaining_ml = MAX(0, MIN(?, remaining_ml - ?)) WHERE id = 1",
            (_MAX_ML, ml),
        )
        await self._conn.commit()

    async def refill(self) -> None:
        now = now_iso()
        await self._conn.execute(
            "UPDATE water_state SET remaining_ml = ?, last_refilled_at = ? WHERE id = 1",
            (_MAX_ML, now),
        )
        await self._conn.commit()
