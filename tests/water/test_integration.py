from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from brew.db import init_db, open_db
from brew.water.repository import WaterSqliteRepository
from brew.water.schema import WATER_SCHEMA


@asynccontextmanager
async def _connect_and_init(path: str):
    conn = await open_db(path)
    try:
        await init_db(conn, [WATER_SCHEMA])
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def file_repo(tmp_path: Path):
    async with _connect_and_init(str(tmp_path / "brew.db")) as conn:
        yield WaterSqliteRepository(conn=conn)


async def test_state_persists_across_connections(tmp_path: Path) -> None:
    db_path = str(tmp_path / "brew.db")

    async with _connect_and_init(db_path) as conn:
        await WaterSqliteRepository(conn=conn).set_remaining_ml(777)

    async with _connect_and_init(db_path) as conn:
        water = await WaterSqliteRepository(conn=conn).get()

    assert water.remaining_ml == 777


async def test_refill_persists(file_repo: WaterSqliteRepository) -> None:
    await file_repo.set_remaining_ml(100)
    await file_repo.refill()
    water = await file_repo.get()
    assert water.remaining_ml == 1500
