"""EventBroadcaster tests — fans events to per-subscriber asyncio.Queue."""

import asyncio
from datetime import UTC, datetime

import pytest

from brew.events.broadcaster import EventBroadcaster
from brew.events.domain import BrewCompleted


@pytest.fixture
def broadcaster() -> EventBroadcaster:
    return EventBroadcaster()


async def test_subscribe_returns_queue_and_receives_events(
    broadcaster: EventBroadcaster,
) -> None:
    queue = broadcaster.subscribe()

    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id="p1",
    )
    await broadcaster.broadcast(event)

    received = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert received == event


async def test_multiple_subscribers_each_receive_event(
    broadcaster: EventBroadcaster,
) -> None:
    q1 = broadcaster.subscribe()
    q2 = broadcaster.subscribe()

    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id=None,
    )
    await broadcaster.broadcast(event)

    assert await asyncio.wait_for(q1.get(), timeout=1.0) == event
    assert await asyncio.wait_for(q2.get(), timeout=1.0) == event


async def test_unsubscribe_drops_queue(broadcaster: EventBroadcaster) -> None:
    queue = broadcaster.subscribe()
    broadcaster.unsubscribe(queue)

    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id=None,
    )
    await broadcaster.broadcast(event)

    assert queue.empty()
