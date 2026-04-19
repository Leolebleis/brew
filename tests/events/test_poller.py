"""DeviceBrewingPoller tests.

The poller splits into `tick()` (one poll iteration — the business logic) and
`run()` (while-loop + error-swallowing + sleep — boilerplate). Tests exercise
tick() directly for deterministic assertions, and check run() separately for
error resilience.
"""

import asyncio
import contextlib
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from brew.events.bus import EventBus
from brew.events.domain import BrewCompleted
from brew.events.poller import DeviceBrewingPoller
from tests.aiden.device.conftest import make_device


@pytest.fixture
def device_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def received() -> list[BrewCompleted]:
    return []


@pytest.fixture
def subscribed_bus(bus: EventBus, received: list[BrewCompleted]) -> EventBus:
    async def handler(event: BrewCompleted) -> None:
        received.append(event)

    bus.subscribe(BrewCompleted, handler)
    return bus


async def test_tick_with_brewing_false_when_never_true_emits_nothing(
    device_service: AsyncMock, subscribed_bus: EventBus, received: list
) -> None:
    device_service.get_device.return_value = make_device(brewing=False)

    poller = DeviceBrewingPoller(device_service=device_service, bus=subscribed_bus)
    await poller.tick()
    await poller.tick()

    assert received == []


async def test_tick_publishes_brew_completed_on_true_to_false(
    device_service: AsyncMock, subscribed_bus: EventBus, received: list
) -> None:
    # Tick 1: brewing=True — poller captures profile_id + brew_start_time.
    # Tick 2: brewing=False — poller detects transition, publishes BrewCompleted.
    device_service.get_device.side_effect = [
        make_device(
            brewing=True,
            brew_start_time=1745000000,
            brew_end_time=None,
            brewing_profile_id="p-1",
        ),
        make_device(
            brewing=False,
            brew_start_time=1745000000,
            brew_end_time=1745000420,
            brewing_profile_id=None,
        ),
    ]

    poller = DeviceBrewingPoller(device_service=device_service, bus=subscribed_bus)
    await poller.tick()
    await poller.tick()

    assert len(received) == 1
    event = received[0]
    assert event.brew_started_at == datetime(2025, 4, 18, 18, 13, 20, tzinfo=UTC)
    assert event.brew_ended_at == datetime(2025, 4, 18, 18, 20, 20, tzinfo=UTC)
    assert event.profile_id == "p-1"


async def test_tick_skips_emission_when_timestamps_incomplete(
    device_service: AsyncMock, subscribed_bus: EventBus, received: list
) -> None:
    device_service.get_device.side_effect = [
        make_device(
            brewing=True,
            brew_start_time=1745000000,
            brewing_profile_id="p-1",
        ),
        make_device(
            brewing=False,
            brew_start_time=1745000000,
            brew_end_time=None,
            brewing_profile_id=None,
        ),
    ]

    poller = DeviceBrewingPoller(device_service=device_service, bus=subscribed_bus)
    await poller.tick()
    await poller.tick()

    assert received == []


async def test_run_swallows_tick_exceptions_and_keeps_looping(
    device_service: AsyncMock, subscribed_bus: EventBus
) -> None:
    device_service.get_device.side_effect = [
        RuntimeError("transient"),
        make_device(brewing=False),
        make_device(brewing=False),
    ]

    # interval_seconds=0 so the loop advances fast.
    poller = DeviceBrewingPoller(device_service=device_service, bus=subscribed_bus, interval_seconds=0)

    task = asyncio.create_task(poller.run())
    for _ in range(10):
        await asyncio.sleep(0)

    assert device_service.get_device.call_count >= 2
    assert not task.done()

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def test_tick_publishes_second_brew_after_recapture(
    device_service: AsyncMock, subscribed_bus: EventBus, received: list
) -> None:
    device_service.get_device.side_effect = [
        make_device(brewing=True, brew_start_time=1, brewing_profile_id="p-1"),
        make_device(brewing=False, brew_start_time=1, brew_end_time=2),
        make_device(brewing=True, brew_start_time=10, brewing_profile_id="p-2"),
        make_device(brewing=False, brew_start_time=10, brew_end_time=20),
    ]

    poller = DeviceBrewingPoller(device_service=device_service, bus=subscribed_bus)
    for _ in range(4):
        await poller.tick()

    assert len(received) == 2
    assert received[0].profile_id == "p-1"
    assert received[1].profile_id == "p-2"
