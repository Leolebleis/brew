from unittest.mock import AsyncMock

from brew.journal.palate import BeanDimensions, PalateQuery, dimension_distance

from tests.journal.conftest import make_entry


def _snap(varietal=None, process=None, roast_level=None, origin=None, altitude_masl=None):
    return {
        "varietal": varietal,
        "process": process,
        "roast_level": roast_level,
        "origin": origin,
        "altitude_masl": altitude_masl,
    }


def test_distance_zero_for_identical_dimensions() -> None:
    q = BeanDimensions(varietal="Geisha", process="natural", roast_level="light")
    d = dimension_distance(q, _snap(varietal="Geisha", process="natural", roast_level="light"), [], [])
    assert d == 0.0


def test_distance_grows_with_mismatch() -> None:
    q = BeanDimensions(varietal="Geisha", process="natural", roast_level="light")
    same = dimension_distance(q, _snap(varietal="Geisha", process="natural", roast_level="light"), [], [])
    diff = dimension_distance(q, _snap(varietal="Bourbon", process="washed", roast_level="dark"), [], [])
    assert diff > same


async def test_tendency_averages_similar_neighbours() -> None:

    entries = [
        make_entry(
            id="e1",
            rating=3,
            acidity=2,
            bitterness=0,
            body=-1,
            sweetness=1,
            strength=0,
            bean_dimensions_snapshot=_snap(varietal="Geisha", process="natural", roast_level="light"),
        ),
        make_entry(
            id="e2",
            rating=4,
            acidity=1,
            bitterness=0,
            body=0,
            sweetness=1,
            strength=0,
            bean_dimensions_snapshot=_snap(varietal="Geisha", process="natural", roast_level="light"),
        ),
        make_entry(
            id="e3",
            rating=4,
            acidity=-2,
            bitterness=2,
            body=2,
            sweetness=0,
            strength=1,
            bean_dimensions_snapshot=_snap(varietal="Robusta", process="washed", roast_level="dark"),
        ),
    ]
    repo = AsyncMock()
    repo.list.return_value = entries
    query = PalateQuery(repo)
    result = await query.tendency_for(BeanDimensions(varietal="Geisha", process="natural", roast_level="light"))
    assert result.n >= 2
    assert result.tendency["acidity"] > 0.5
    assert result.confidence > 0.0


async def test_tendency_empty_when_no_rated_history() -> None:
    repo = AsyncMock()
    repo.list.return_value = []
    result = await PalateQuery(repo).tendency_for(BeanDimensions(varietal="Geisha"))
    assert result.n == 0
    assert result.confidence == 0.0
    assert result.tendency == {}
