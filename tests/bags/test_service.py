from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from brew.bags.model.bag import BagUpdate
from brew.bags.service import BagService
from brew.errors import NotFoundError
from brew.events.bus import EventBus
from brew.events.domain import BagActivated, BagFinished
from tests.bags.conftest import make_bag, make_bag_create


async def test_create_delegates_to_repository() -> None:
    mock_repo = AsyncMock()
    expected = make_bag(id="b1")
    mock_repo.create.return_value = expected

    service = BagService(repo=mock_repo, bus=EventBus())
    create = make_bag_create()
    result = await service.create(create)

    assert result == expected
    mock_repo.create.assert_awaited_once_with(create)


async def test_get_returns_bag() -> None:
    mock_repo = AsyncMock()
    mock_repo.get.return_value = make_bag(id="b1")

    service = BagService(repo=mock_repo, bus=EventBus())
    result = await service.get("b1")

    assert result.id == "b1"


async def test_get_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.get.return_value = None

    service = BagService(repo=mock_repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.get("nope")


async def test_list_delegates_with_filters() -> None:
    mock_repo = AsyncMock()
    mock_repo.list.return_value = []

    service = BagService(repo=mock_repo, bus=EventBus())
    await service.list(active=True, roaster="Onyx")

    mock_repo.list.assert_awaited_once_with(active=True, finished=None, roaster="Onyx", origin=None, name=None)


async def test_get_active_returns_active_bag_or_none() -> None:
    mock_repo = AsyncMock()
    mock_repo.get_active.return_value = make_bag(id="a1", is_active=True)

    service = BagService(repo=mock_repo, bus=EventBus())
    result = await service.get_active()

    assert result is not None
    assert result.id == "a1"


async def test_update_raises_not_found_when_bag_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.update.return_value = False

    service = BagService(repo=mock_repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.update("nope", BagUpdate(name="X"))


async def test_update_succeeds_when_bag_exists() -> None:
    mock_repo = AsyncMock()
    mock_repo.update.return_value = True

    service = BagService(repo=mock_repo, bus=EventBus())
    await service.update("b1", BagUpdate(name="X"))

    mock_repo.update.assert_awaited_once()


async def test_delete_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.delete.return_value = False

    service = BagService(repo=mock_repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.delete("nope")


async def test_activate_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.activate.return_value = False

    service = BagService(repo=mock_repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.activate("nope")


async def test_activate_publishes_bag_activated() -> None:
    mock_repo = AsyncMock()
    mock_repo.activate.return_value = True
    activated_bag = make_bag(id="b1", name="Daybreak", is_active=True)
    mock_repo.get.return_value = activated_bag

    bus = EventBus()
    received: list[BagActivated] = []
    bus.subscribe(BagActivated, lambda e: _append(received, e))

    service = BagService(repo=mock_repo, bus=bus)
    await service.activate("b1")

    assert received == [BagActivated(bag_id="b1", name="Daybreak")]


async def test_zero_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.zero.return_value = False

    service = BagService(repo=mock_repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.zero("nope")


async def test_zero_publishes_bag_finished() -> None:
    mock_repo = AsyncMock()
    mock_repo.zero.return_value = True

    bus = EventBus()
    received: list[BagFinished] = []
    bus.subscribe(BagFinished, lambda e: _append(received, e))

    service = BagService(repo=mock_repo, bus=bus)
    await service.zero("b1")

    assert received == [BagFinished(bag_id="b1")]


async def test_decrement_delegates_to_repo_when_match() -> None:
    mock_repo = AsyncMock()
    mock_repo.decrement.return_value = True
    # decrement reads back to check finished state — return non-finished bag
    mock_repo.get.return_value = make_bag(id="b1", remaining_grams=100, finished_at=None)

    service = BagService(repo=mock_repo, bus=EventBus())
    await service.decrement("b1", 21)

    mock_repo.decrement.assert_awaited_once_with("b1", 21)


async def test_decrement_to_zero_publishes_bag_finished() -> None:
    mock_repo = AsyncMock()
    mock_repo.decrement.return_value = True
    mock_repo.get.return_value = make_bag(
        id="b1",
        remaining_grams=0,
        finished_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC),
    )

    bus = EventBus()
    received: list[BagFinished] = []
    bus.subscribe(BagFinished, lambda e: _append(received, e))

    service = BagService(repo=mock_repo, bus=bus)
    await service.decrement("b1", 250)

    assert received == [BagFinished(bag_id="b1")]


async def test_decrement_noop_when_already_finished() -> None:
    # decrement returns False (already finished) → service confirms bag exists, no-op
    mock_repo = AsyncMock()
    mock_repo.decrement.return_value = False
    mock_repo.get.return_value = make_bag(id="b1")

    service = BagService(repo=mock_repo, bus=EventBus())
    await service.decrement("b1", 21)

    mock_repo.get.assert_awaited_once_with("b1")


async def test_decrement_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.decrement.return_value = False
    mock_repo.get.return_value = None

    service = BagService(repo=mock_repo, bus=EventBus())
    with pytest.raises(NotFoundError):
        await service.decrement("nope", 21)


async def _append(received: list, event: object) -> None:
    received.append(event)
