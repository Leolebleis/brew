from datetime import date

import pytest

from brew.bags.model.bag import BagUpdate
from brew.bags.repository import BagSqliteRepository
from brew.bags.schema import BAGS_SCHEMA
from brew.db import init_db, open_db
from tests.bags.conftest import make_bag_create


@pytest.fixture
async def repo():
    conn = await open_db(":memory:")
    await init_db(conn, [BAGS_SCHEMA])
    yield BagSqliteRepository(conn=conn)
    await conn.close()


async def test_create_returns_bag_with_id_and_defaults(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(name="Daybreak"))

    assert created.id
    assert created.name == "Daybreak"
    assert created.remaining_grams == 250
    assert created.is_active is False
    assert created.finished_at is None
    assert created.profile_snapshot == {"ratio": 60.0}


async def test_get_returns_existing_bag(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create())
    fetched = await repo.get(created.id)
    assert fetched == created


async def test_get_returns_none_for_missing(repo: BagSqliteRepository) -> None:
    assert await repo.get("does-not-exist") is None


async def test_list_returns_all_bags(repo: BagSqliteRepository) -> None:
    await repo.create(make_bag_create(name="Daybreak"))
    await repo.create(make_bag_create(name="Moonrise"))

    bags = await repo.list()

    assert {b.name for b in bags} == {"Daybreak", "Moonrise"}


async def test_list_filters_by_roaster(repo: BagSqliteRepository) -> None:
    await repo.create(make_bag_create(name="Daybreak", roaster="Intermission"))
    await repo.create(make_bag_create(name="Moonrise", roaster="Onyx"))

    bags = await repo.list(roaster="Onyx")

    assert len(bags) == 1
    assert bags[0].name == "Moonrise"


async def test_list_filters_by_origin(repo: BagSqliteRepository) -> None:
    await repo.create(make_bag_create(name="Daybreak", origin="Ethiopia"))
    await repo.create(make_bag_create(name="Moonrise", origin="Colombia"))

    bags = await repo.list(origin="Colombia")

    assert len(bags) == 1
    assert bags[0].name == "Moonrise"


async def test_get_active_returns_none_when_no_active_bag(repo: BagSqliteRepository) -> None:
    await repo.create(make_bag_create())
    assert await repo.get_active() is None


async def test_create_persists_roast_date_as_date(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(roast_date=date(2026, 3, 15)))
    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.roast_date == date(2026, 3, 15)


async def test_update_changes_fields(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(name="Daybreak"))

    await repo.update(created.id, BagUpdate(name="Nightfall", roast_level="dark"))
    updated = await repo.get(created.id)

    assert updated is not None
    assert updated.name == "Nightfall"
    assert updated.roast_level == "dark"
    assert updated.origin == "Ethiopia, Yirgacheffe"  # unchanged


async def test_update_preserves_profile_snapshot_when_not_provided(
    repo: BagSqliteRepository,
) -> None:
    created = await repo.create(make_bag_create(profile_snapshot={"ratio": 60.0}))

    await repo.update(created.id, BagUpdate(name="Renamed"))
    updated = await repo.get(created.id)

    assert updated is not None
    assert updated.profile_snapshot == {"ratio": 60.0}


async def test_update_replaces_profile_snapshot_when_provided(
    repo: BagSqliteRepository,
) -> None:
    created = await repo.create(make_bag_create(profile_snapshot={"ratio": 60.0}))

    await repo.update(created.id, BagUpdate(profile_snapshot={"ratio": 55.0, "bloom": 30}))
    updated = await repo.get(created.id)

    assert updated is not None
    assert updated.profile_snapshot == {"ratio": 55.0, "bloom": 30}


async def test_update_missing_bag_returns_false(repo: BagSqliteRepository) -> None:
    result = await repo.update("does-not-exist", BagUpdate(name="X"))
    assert result is False


async def test_delete_removes_bag(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create())
    await repo.delete(created.id)
    assert await repo.get(created.id) is None


async def test_delete_missing_returns_false(repo: BagSqliteRepository) -> None:
    assert await repo.delete("does-not-exist") is False
