import pytest

from brew.db import init_db, open_db
from brew.water.repository import WaterSqliteRepository
from brew.water.schema import WATER_SCHEMA


@pytest.fixture
async def repo():
    conn = await open_db(":memory:")
    await init_db(conn, [WATER_SCHEMA])
    yield WaterSqliteRepository(conn=conn)
    await conn.close()


async def test_get_returns_seeded_default_of_1500ml(repo: WaterSqliteRepository) -> None:
    water = await repo.get()
    assert water.remaining_ml == 1500


async def test_refill_resets_to_1500_and_updates_timestamp(repo: WaterSqliteRepository) -> None:
    await repo.set_remaining_ml(300)
    before = await repo.get()
    assert before.remaining_ml == 300

    await repo.refill()
    after = await repo.get()
    assert after.remaining_ml == 1500
    assert after.last_refilled_at > before.last_refilled_at


async def test_set_remaining_ml_clamps_below_zero(repo: WaterSqliteRepository) -> None:
    await repo.set_remaining_ml(-50)
    water = await repo.get()
    assert water.remaining_ml == 0


async def test_set_remaining_ml_clamps_above_1500(repo: WaterSqliteRepository) -> None:
    await repo.set_remaining_ml(99999)
    water = await repo.get()
    assert water.remaining_ml == 1500
