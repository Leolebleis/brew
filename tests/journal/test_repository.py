from datetime import UTC, datetime

import pytest

from brew.db import init_db, open_db
from brew.journal.repository import JournalSqliteRepository
from brew.journal.schema import JOURNAL_SCHEMA
from tests.journal.conftest import make_entry_create


@pytest.fixture
async def repo():
    conn = await open_db(":memory:")
    await init_db(conn, [JOURNAL_SCHEMA])
    yield JournalSqliteRepository(conn=conn)
    await conn.close()


async def test_create_returns_entry_with_id_and_null_rating(repo: JournalSqliteRepository) -> None:
    created = await repo.create(make_entry_create())

    assert created.id
    assert created.rating is None
    assert created.note_text is None
    assert created.water_ml == 500
    assert created.profile_snapshot_at_brew == {"ratio": 60.0, "bloom_duration": 30}


async def test_get_returns_existing_entry(repo: JournalSqliteRepository) -> None:
    created = await repo.create(make_entry_create())
    fetched = await repo.get(created.id)
    assert fetched == created


async def test_get_returns_none_for_missing(repo: JournalSqliteRepository) -> None:
    assert await repo.get("does-not-exist") is None


async def test_list_returns_entries_newest_first(repo: JournalSqliteRepository) -> None:
    older = await repo.create(make_entry_create(brew_ended_at=datetime(2026, 4, 17, 7, 0, 0, tzinfo=UTC)))
    newer = await repo.create(make_entry_create(brew_ended_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC)))

    entries = await repo.list()

    assert [e.id for e in entries] == [newer.id, older.id]


async def test_list_filters_by_bag_id(repo: JournalSqliteRepository) -> None:
    await repo.create(make_entry_create(bag_id="bag-a"))
    await repo.create(make_entry_create(bag_id="bag-b"))

    entries = await repo.list(bag_id="bag-a")

    assert len(entries) == 1
    assert entries[0].bag_id == "bag-a"


async def test_list_filters_by_profile_id(repo: JournalSqliteRepository) -> None:
    await repo.create(make_entry_create(profile_id="p-a"))
    await repo.create(make_entry_create(profile_id="p-b"))

    entries = await repo.list(profile_id="p-b")

    assert len(entries) == 1
    assert entries[0].profile_id == "p-b"


async def test_list_filters_since_datetime(repo: JournalSqliteRepository) -> None:
    await repo.create(make_entry_create(brew_ended_at=datetime(2026, 4, 17, 7, 0, 0, tzinfo=UTC)))
    newer = await repo.create(make_entry_create(brew_ended_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC)))

    entries = await repo.list(since=datetime(2026, 4, 18, 0, 0, 0, tzinfo=UTC))

    assert len(entries) == 1
    assert entries[0].id == newer.id


async def test_list_filters_rating_min(repo: JournalSqliteRepository) -> None:
    low = await repo.create(make_entry_create())
    high = await repo.create(make_entry_create())
    await repo.update(low.id, rating=2, note_text=None)
    await repo.update(high.id, rating=5, note_text=None)

    entries = await repo.list(rating_min=4)

    assert len(entries) == 1
    assert entries[0].id == high.id


async def test_list_respects_limit(repo: JournalSqliteRepository) -> None:
    for i in range(5):
        await repo.create(make_entry_create(brew_ended_at=datetime(2026, 4, 18, 7, i, 0, tzinfo=UTC)))

    entries = await repo.list(limit=3)

    assert len(entries) == 3
