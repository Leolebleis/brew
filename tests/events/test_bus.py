from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from brew.events.bus import EventBus
from brew.events.domain import BrewCompleted


@dataclass(frozen=True)
class _OtherEvent:
    payload: str


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


async def test_publish_with_no_subscribers_is_noop(bus: EventBus) -> None:
    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id="p1",
    )
    await bus.publish(event)  # must not raise


async def test_subscribe_then_publish_invokes_handler(bus: EventBus) -> None:
    received: list[BrewCompleted] = []

    async def handler(event: BrewCompleted) -> None:
        received.append(event)

    bus.subscribe(BrewCompleted, handler)
    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id="p1",
    )

    await bus.publish(event)

    assert received == [event]


async def test_multiple_handlers_for_same_event_all_fire(bus: EventBus) -> None:
    calls_a: list[str] = []
    calls_b: list[str] = []

    async def handler_a(_event: BrewCompleted) -> None:
        calls_a.append("a")

    async def handler_b(_event: BrewCompleted) -> None:
        calls_b.append("b")

    bus.subscribe(BrewCompleted, handler_a)
    bus.subscribe(BrewCompleted, handler_b)

    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id=None,
    )
    await bus.publish(event)

    assert calls_a == ["a"]
    assert calls_b == ["b"]


async def test_handlers_for_different_event_types_are_isolated(bus: EventBus) -> None:
    brew_received: list[object] = []
    other_received: list[object] = []

    async def brew_handler(event: BrewCompleted) -> None:
        brew_received.append(event)

    async def other_handler(event: _OtherEvent) -> None:
        other_received.append(event)

    bus.subscribe(BrewCompleted, brew_handler)
    bus.subscribe(_OtherEvent, other_handler)

    await bus.publish(_OtherEvent(payload="x"))

    assert brew_received == []
    assert len(other_received) == 1


async def test_handler_exception_does_not_prevent_other_handlers(
    bus: EventBus,
) -> None:
    good_fired: list[bool] = []

    async def failing(_event: BrewCompleted) -> None:
        msg = "boom"
        raise RuntimeError(msg)

    async def good(_event: BrewCompleted) -> None:
        good_fired.append(True)

    bus.subscribe(BrewCompleted, failing)
    bus.subscribe(BrewCompleted, good)

    event = BrewCompleted(
        brew_started_at=datetime(2026, 4, 19, 7, 0, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 4, 19, 7, 7, 0, tzinfo=UTC),
        profile_id=None,
    )

    await bus.publish(event)  # must not raise — failing handler is isolated

    assert good_fired == [True]
