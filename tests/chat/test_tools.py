from datetime import UTC, datetime
from unittest.mock import AsyncMock

from brew.chat.tools import make_find_historical_bag, make_query_journal
from tests.bags.conftest import make_bag
from tests.journal.conftest import make_entry


async def test_query_journal_passes_filters() -> None:
    journal_service = AsyncMock()
    journal_service.list = AsyncMock(return_value=[])

    tool = make_query_journal(journal_service)
    await tool(bag_id="b1", profile_id="p1", rating_min=4, limit=5)

    journal_service.list.assert_awaited_once_with(
        bag_id="b1",
        profile_id="p1",
        since=None,
        rating_min=4,
        limit=5,
    )


async def test_query_journal_serializes_dates_to_iso_strings() -> None:
    when = datetime(2026, 4, 19, 8, 30, tzinfo=UTC)
    entry = make_entry(
        id="e1",
        brew_started_at=when,
        brew_ended_at=when,
        bag_id="b1",
        profile_id="p1",
        water_ml=300,
        dose_grams=18,
        rating=5,
        note_text="great",
    )
    journal_service = AsyncMock()
    journal_service.list = AsyncMock(return_value=[entry])

    result = await make_query_journal(journal_service)()

    assert result == [
        {
            "id": "e1",
            "brew_ended_at": when.isoformat(),
            "bag_id": "b1",
            "profile_id": "p1",
            "water_ml": 300,
            "dose_grams": 18,
            "rating": 5,
            "note_text": "great",
        }
    ]


async def test_find_historical_bag_filters_by_name_in_python() -> None:
    bag_match = make_bag(id="bag-match", name="match")
    bag_other = make_bag(id="bag-other", name="other")

    bag_service = AsyncMock()
    bag_service.list = AsyncMock(return_value=[bag_match, bag_other])

    tool = make_find_historical_bag(bag_service)
    result = await tool(name="match")

    # name filter is applied in Python, not forwarded to bag_service
    bag_service.list.assert_awaited_once_with(roaster=None, origin=None)
    assert len(result) == 1
    assert result[0]["id"] == "bag-match"
    assert result[0]["name"] == "match"


async def test_find_historical_bag_serializes_profile_snapshot_unchanged() -> None:
    snapshot = {"ratio": 60.0, "bloom_duration": 30, "temp_c": 93}
    bag = make_bag(profile_snapshot=snapshot)

    bag_service = AsyncMock()
    bag_service.list = AsyncMock(return_value=[bag])

    result = await make_find_historical_bag(bag_service)()

    assert result[0]["profile_snapshot"] == snapshot
    assert result[0]["profile_snapshot"] is snapshot
