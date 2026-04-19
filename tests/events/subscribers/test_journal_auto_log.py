"""Tests for the BrewCompleted → journal auto-log subscriber."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

from brew.events.domain import BrewCompleted
from brew.events.subscribers.journal_auto_log import make_journal_auto_log_handler
from brew.journal.model.entry import JournalEntryCreate
from tests.bags.conftest import make_bag


def _event(profile_id: str | None = "p-1") -> BrewCompleted:
    return BrewCompleted(
        brew_started_at=datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
        profile_id=profile_id,
    )


async def test_handles_matching_active_bag() -> None:
    journal_service = AsyncMock()
    bag_service = AsyncMock()
    bag_service.get_active.return_value = make_bag(
        id="bag-active",
        profile_id="p-1",
        profile_snapshot={"target_volume": 330, "ratio": 15.5},
    )

    handler = make_journal_auto_log_handler(journal_service, bag_service)
    await handler(_event(profile_id="p-1"))

    journal_service.create.assert_awaited_once()
    arg = journal_service.create.await_args.args[0]
    assert isinstance(arg, JournalEntryCreate)
    assert arg.bag_id == "bag-active"
    assert arg.profile_id == "p-1"
    assert arg.water_ml == 330
    assert arg.dose_grams == 21  # int(330 / 15.5)
    assert arg.profile_snapshot_at_brew == {"target_volume": 330, "ratio": 15.5}
    assert arg.brew_started_at == datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC)
    assert arg.brew_ended_at == datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC)


async def test_handles_no_active_bag() -> None:
    journal_service = AsyncMock()
    bag_service = AsyncMock()
    bag_service.get_active.return_value = None

    handler = make_journal_auto_log_handler(journal_service, bag_service)
    await handler(_event(profile_id="p-1"))

    journal_service.create.assert_awaited_once()
    arg = journal_service.create.await_args.args[0]
    assert arg.bag_id is None
    assert arg.profile_id == "p-1"
    assert arg.water_ml == 0
    assert arg.dose_grams == 0
    assert arg.profile_snapshot_at_brew == {}


async def test_handles_profile_mismatch() -> None:
    journal_service = AsyncMock()
    bag_service = AsyncMock()
    bag_service.get_active.return_value = make_bag(
        id="bag-other",
        profile_id="p-X",
        profile_snapshot={"target_volume": 330, "ratio": 15.5},
    )

    handler = make_journal_auto_log_handler(journal_service, bag_service)
    await handler(_event(profile_id="p-Y"))

    journal_service.create.assert_awaited_once()
    arg = journal_service.create.await_args.args[0]
    assert arg.bag_id is None
    assert arg.profile_id == "p-Y"
    assert arg.water_ml == 0
    assert arg.dose_grams == 0
    assert arg.profile_snapshot_at_brew == {}


async def test_handles_missing_profile_snapshot_fields() -> None:
    journal_service = AsyncMock()
    bag_service = AsyncMock()
    bag_service.get_active.return_value = make_bag(
        id="bag-empty",
        profile_id="p-1",
        profile_snapshot={},
    )

    handler = make_journal_auto_log_handler(journal_service, bag_service)
    await handler(_event(profile_id="p-1"))

    journal_service.create.assert_awaited_once()
    arg = journal_service.create.await_args.args[0]
    assert arg.bag_id == "bag-empty"
    assert arg.water_ml == 0
    assert arg.dose_grams == 0
