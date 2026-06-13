import aiosqlite

from brew.bags.model.bag import BagCreate, BagUpdate
from brew.bags.repository import BagSqliteRepository
from brew.bags.schema import BAGS_SCHEMA


async def _repo() -> BagSqliteRepository:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    for ddl in BAGS_SCHEMA:
        await conn.execute(ddl)
    await conn.commit()
    return BagSqliteRepository(conn)


async def test_create_persists_bean_dimensions() -> None:
    repo = await _repo()
    bag = await repo.create(
        BagCreate(
            name="Spring Bloom",
            origin="Huila",
            roaster="Intermission",
            roast_level="light",
            initial_grams=250,
            profile_snapshot={},
            varietal="Geisha",
            process="natural",
            altitude_masl=1650,
        )
    )
    assert bag.varietal == "Geisha"
    assert bag.process == "natural"
    assert bag.altitude_masl == 1650


async def test_update_changes_dimensions() -> None:
    repo = await _repo()
    bag = await repo.create(
        BagCreate(name="x", origin="o", roaster="r", roast_level="light", initial_grams=250, profile_snapshot={})
    )
    assert bag.varietal is None
    await repo.update(bag.id, BagUpdate(varietal="Bourbon", process="washed"))
    refreshed = await repo.get(bag.id)
    assert refreshed.varietal == "Bourbon"
    assert refreshed.process == "washed"
