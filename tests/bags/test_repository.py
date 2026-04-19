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


async def test_activate_sets_is_active(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create())

    ok = await repo.activate(created.id)
    assert ok is True

    active = await repo.get_active()
    assert active is not None
    assert active.id == created.id


async def test_activate_deactivates_previous_active(repo: BagSqliteRepository) -> None:
    first = await repo.create(make_bag_create(name="First"))
    second = await repo.create(make_bag_create(name="Second"))

    await repo.activate(first.id)
    await repo.activate(second.id)

    active = await repo.get_active()
    assert active is not None
    assert active.id == second.id

    first_reloaded = await repo.get(first.id)
    assert first_reloaded is not None
    assert first_reloaded.is_active is False


async def test_activate_missing_returns_false(repo: BagSqliteRepository) -> None:
    assert await repo.activate("does-not-exist") is False


async def test_zero_sets_remaining_to_zero_and_finishes(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(initial_grams=250))
    await repo.activate(created.id)

    ok = await repo.zero(created.id)
    assert ok is True

    zeroed = await repo.get(created.id)
    assert zeroed is not None
    assert zeroed.remaining_grams == 0
    assert zeroed.is_active is False
    assert zeroed.finished_at is not None


async def test_zero_missing_returns_false(repo: BagSqliteRepository) -> None:
    assert await repo.zero("does-not-exist") is False


async def test_set_remaining_grams_clamps_below_zero(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(initial_grams=250))
    await repo.set_remaining_grams(created.id, -50)
    updated = await repo.get(created.id)
    assert updated is not None
    assert updated.remaining_grams == 0


async def test_set_remaining_grams_missing_returns_false(repo: BagSqliteRepository) -> None:
    assert await repo.set_remaining_grams("does-not-exist", 100) is False


async def test_decrement_subtracts_in_a_single_statement(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(initial_grams=250))

    ok = await repo.decrement(created.id, 21)
    assert ok is True

    updated = await repo.get(created.id)
    assert updated is not None
    assert updated.remaining_grams == 229
    assert updated.finished_at is None


async def test_decrement_zeros_and_finishes_when_reaching_empty(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(initial_grams=20))
    await repo.activate(created.id)

    ok = await repo.decrement(created.id, 50)
    assert ok is True

    finished = await repo.get(created.id)
    assert finished is not None
    assert finished.remaining_grams == 0
    assert finished.is_active is False
    assert finished.finished_at is not None


async def test_decrement_missing_returns_false(repo: BagSqliteRepository) -> None:
    assert await repo.decrement("does-not-exist", 21) is False


async def test_decrement_already_finished_returns_false(repo: BagSqliteRepository) -> None:
    created = await repo.create(make_bag_create(initial_grams=10))
    await repo.zero(created.id)

    assert await repo.decrement(created.id, 5) is False
    # finished_at should NOT have been bumped
    finished = await repo.get(created.id)
    assert finished is not None
    assert finished.remaining_grams == 0
