"""Tests for the JournalEntryCreated → water decrement subscriber."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

from brew.events.domain import JournalEntryCreated
from brew.events.subscribers.water_decrement import make_water_decrement_handler


def _event(water_ml: int = 330) -> JournalEntryCreated:
    return JournalEntryCreated(
        entry_id="e-1",
        brew_started_at=datetime(2026, 4, 18, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 18, 7, 7, 0, tzinfo=UTC),
        bag_id="bag-1",
        profile_id="p-1",
        water_ml=water_ml,
        dose_grams=21,
    )


async def test_decrements_when_water_ml_positive() -> None:
    water_service = AsyncMock()

    handler = make_water_decrement_handler(water_service)
    await handler(_event(water_ml=330))

    water_service.decrement.assert_awaited_once_with(330)


async def test_skips_when_water_ml_zero() -> None:
    water_service = AsyncMock()

    handler = make_water_decrement_handler(water_service)
    await handler(_event(water_ml=0))

    water_service.decrement.assert_not_awaited()


async def test_skips_when_water_ml_negative() -> None:
    water_service = AsyncMock()

    handler = make_water_decrement_handler(water_service)
    await handler(_event(water_ml=-50))

    water_service.decrement.assert_not_awaited()
