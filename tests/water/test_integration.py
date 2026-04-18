from pathlib import Path

import pytest

from brew.db import init_db, open_db
from brew.water.repository import WaterSqliteRepository
from brew.water.schema import WATER_SCHEMA


@pytest.fixture
async def file_repo(tmp_path: Path):
    db_path = tmp_path / "brew.db"
    conn = await open_db(str(db_path))
    await init_db(conn, [WATER_SCHEMA])
    yield WaterSqliteRepository(conn=conn)
    await conn.close()


async def test_state_persists_across_connections(tmp_path: Path) -> None:
    db_path = tmp_path / "brew.db"

    conn1 = await open_db(str(db_path))
    await init_db(conn1, [WATER_SCHEMA])
    repo1 = WaterSqliteRepository(conn=conn1)
    await repo1.set_remaining_ml(777)
    await conn1.close()

    conn2 = await open_db(str(db_path))
    await init_db(conn2, [WATER_SCHEMA])  # idempotent — CREATE IF NOT EXISTS + INSERT OR IGNORE
    repo2 = WaterSqliteRepository(conn=conn2)
    water = await repo2.get()
    await conn2.close()

    assert water.remaining_ml == 777


async def test_refill_persists(file_repo: WaterSqliteRepository) -> None:
    await file_repo.set_remaining_ml(100)
    await file_repo.refill()
    water = await file_repo.get()
    assert water.remaining_ml == 1500
