"""Tests for the JournalEntryCreated → bag decrement subscriber."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

from brew.errors import NotFoundError
from brew.events.domain import JournalEntryCreated
from brew.events.subscribers.bag_decrement import make_bag_decrement_handler


def _event(bag_id: str | None = "bag-1", dose_grams: int = 21) -> JournalEntryCreated:
    return JournalEntryCreated(
        entry_id="e-1",
        brew_started_at=datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
        bag_id=bag_id,
        profile_id="p-1",
        water_ml=330,
        dose_grams=dose_grams,
    )


async def test_decrements_when_bag_id_and_dose_present() -> None:
    bag_service = AsyncMock()

    handler = make_bag_decrement_handler(bag_service)
    await handler(_event(bag_id="bag-1", dose_grams=21))

    bag_service.decrement.assert_awaited_once_with("bag-1", 21)


async def test_skips_when_bag_id_none() -> None:
    bag_service = AsyncMock()

    handler = make_bag_decrement_handler(bag_service)
    await handler(_event(bag_id=None, dose_grams=21))

    bag_service.decrement.assert_not_awaited()


async def test_skips_when_dose_zero() -> None:
    bag_service = AsyncMock()

    handler = make_bag_decrement_handler(bag_service)
    await handler(_event(bag_id="bag-1", dose_grams=0))

    bag_service.decrement.assert_not_awaited()


async def test_swallows_not_found_error() -> None:
    bag_service = AsyncMock()
    bag_service.decrement.side_effect = NotFoundError(
        message="Bag bag-gone not found",
        resource_kind="bag",
        resource_id="bag-gone",
    )

    handler = make_bag_decrement_handler(bag_service)
    await handler(_event(bag_id="bag-gone", dose_grams=21))

    bag_service.decrement.assert_awaited_once()
