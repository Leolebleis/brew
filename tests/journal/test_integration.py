from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest

from brew.db import init_db, open_db
from brew.journal.repository import JournalSqliteRepository
from brew.journal.schema import JOURNAL_SCHEMA
from tests.journal.conftest import make_entry_create


@asynccontextmanager
async def _connect_and_init(path: str):
    conn = await open_db(path)
    try:
        await init_db(conn, [JOURNAL_SCHEMA])
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def file_repo(tmp_path: Path):
    async with _connect_and_init(str(tmp_path / "brew.db")) as conn:
        yield JournalSqliteRepository(conn=conn)


async def test_entry_persists_across_connections(tmp_path: Path) -> None:
    db_path = str(tmp_path / "brew.db")

    async with _connect_and_init(db_path) as conn:
        repo = JournalSqliteRepository(conn=conn)
        created = await repo.create(make_entry_create(water_ml=350))

    async with _connect_and_init(db_path) as conn:
        fetched = await JournalSqliteRepository(conn=conn).get(created.id)

    assert fetched is not None
    assert fetched.water_ml == 350
    assert fetched.profile_snapshot_at_brew == {"ratio": 60.0, "bloom_duration": 30}


async def test_rating_and_note_persist(file_repo: JournalSqliteRepository) -> None:
    created = await file_repo.create(make_entry_create())

    await file_repo.update(created.id, rating=4, note_text="Caramel and orange peel")

    reloaded = await file_repo.get(created.id)
    assert reloaded is not None
    assert reloaded.rating == 4
    assert reloaded.note_text == "Caramel and orange peel"


async def test_list_ordering_is_newest_first_across_many_entries(
    file_repo: JournalSqliteRepository,
) -> None:
    for i in range(5):
        await file_repo.create(make_entry_create(brew_ended_at=datetime(2026, 4, 18, 7, i, 0, tzinfo=UTC)))

    entries = await file_repo.list()

    assert len(entries) == 5
    # Minutes ordered 4, 3, 2, 1, 0 → newest first
    assert [e.brew_ended_at.minute for e in entries] == [4, 3, 2, 1, 0]
