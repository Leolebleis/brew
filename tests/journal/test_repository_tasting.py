from datetime import UTC, datetime

import aiosqlite

from brew.journal.model.entry import JournalEntryCreate, TastingAxes
from brew.journal.repository import JournalSqliteRepository
from brew.journal.schema import JOURNAL_SCHEMA


async def _repo() -> JournalSqliteRepository:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    for ddl in JOURNAL_SCHEMA:
        await conn.execute(ddl)
    await conn.commit()
    return JournalSqliteRepository(conn)


def _make_create(**kw) -> JournalEntryCreate:
    base: dict = {
        "brew_started_at": datetime(2026, 6, 13, 7, 0, tzinfo=UTC),
        "brew_ended_at": datetime(2026, 6, 13, 7, 7, tzinfo=UTC),
        "bag_id": "b1",
        "profile_id": "p1",
        "profile_snapshot_at_brew": {},
        "water_ml": 450,
        "dose_grams": 27,
    }
    base.update(kw)
    return JournalEntryCreate(**base)


async def test_new_entry_has_empty_tags_and_null_axes() -> None:
    repo = await _repo()
    entry = await repo.create(_make_create())
    assert entry.flavor_tags == []
    assert entry.acidity is None
    assert entry.bean_dimensions_snapshot is None


async def test_record_tasting_persists_axes_tags_snapshot() -> None:
    repo = await _repo()
    entry = await repo.create(_make_create())
    ok = await repo.record_tasting(
        entry.id,
        axes=TastingAxes(acidity=2, bitterness=0, body=-1, sweetness=1, strength=0),
        flavor_tags=["floral", "berry"],
        note_text="sharp, hollow middle",
        rating=3,
        bean_dimensions_snapshot={"varietal": "Geisha", "process": "natural", "roast_level": "light"},
    )
    assert ok is True
    refreshed = await repo.get(entry.id)
    assert refreshed.acidity == 2
    assert refreshed.sweetness == 1
    assert refreshed.flavor_tags == ["floral", "berry"]
    assert refreshed.note_text == "sharp, hollow middle"
    assert refreshed.rating == 3
    assert refreshed.bean_dimensions_snapshot["varietal"] == "Geisha"
