from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from brew.bags.repository import BagSqliteRepository
from brew.bags.schema import BAGS_SCHEMA
from brew.db import init_db, open_db
from tests.bags.conftest import make_bag_create


@asynccontextmanager
async def _connect_and_init(path: str):
    conn = await open_db(path)
    try:
        await init_db(conn, [BAGS_SCHEMA])
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def file_repo(tmp_path: Path):
    async with _connect_and_init(str(tmp_path / "brew.db")) as conn:
        yield BagSqliteRepository(conn=conn)


async def test_bag_persists_across_connections(tmp_path: Path) -> None:
    db_path = str(tmp_path / "brew.db")

    async with _connect_and_init(db_path) as conn:
        repo = BagSqliteRepository(conn=conn)
        created = await repo.create(make_bag_create(name="Daybreak"))

    async with _connect_and_init(db_path) as conn:
        fetched = await BagSqliteRepository(conn=conn).get(created.id)

    assert fetched is not None
    assert fetched.name == "Daybreak"


async def test_activate_deactivates_previous_across_connections(
    tmp_path: Path,
) -> None:
    db_path = str(tmp_path / "brew.db")

    async with _connect_and_init(db_path) as conn:
        repo = BagSqliteRepository(conn=conn)
        first = await repo.create(make_bag_create(name="First"))
        second = await repo.create(make_bag_create(name="Second"))
        await repo.activate(first.id)

    async with _connect_and_init(db_path) as conn:
        repo = BagSqliteRepository(conn=conn)
        await repo.activate(second.id)

    async with _connect_and_init(db_path) as conn:
        active = await BagSqliteRepository(conn=conn).get_active()
        assert active is not None
        assert active.name == "Second"
        first_reloaded = await BagSqliteRepository(conn=conn).get(first.id)
        assert first_reloaded is not None
        assert first_reloaded.is_active is False


async def test_zero_persists_finished_at(file_repo: BagSqliteRepository) -> None:
    created = await file_repo.create(make_bag_create())
    await file_repo.activate(created.id)
    await file_repo.zero(created.id)

    reloaded = await file_repo.get(created.id)
    assert reloaded is not None
    assert reloaded.remaining_grams == 0
    assert reloaded.is_active is False
    assert reloaded.finished_at is not None
