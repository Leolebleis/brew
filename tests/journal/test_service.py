from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from brew.errors import NotFoundError
from brew.journal.service import JournalService
from tests.journal.conftest import make_entry, make_entry_create


async def test_create_from_brew_event_delegates_to_repo() -> None:
    mock_repo = AsyncMock()
    expected = make_entry(id="e1")
    mock_repo.create.return_value = expected

    service = JournalService(repo=mock_repo)
    create = make_entry_create()
    result = await service.create_from_brew_event(create)

    assert result == expected
    mock_repo.create.assert_awaited_once_with(create)


async def test_get_returns_entry() -> None:
    mock_repo = AsyncMock()
    mock_repo.get.return_value = make_entry(id="e1")

    service = JournalService(repo=mock_repo)
    result = await service.get("e1")

    assert result.id == "e1"


async def test_get_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.get.return_value = None

    service = JournalService(repo=mock_repo)
    with pytest.raises(NotFoundError):
        await service.get("nope")


async def test_list_delegates_with_filters() -> None:
    mock_repo = AsyncMock()
    mock_repo.list.return_value = []

    service = JournalService(repo=mock_repo)
    since = datetime(2026, 4, 1, tzinfo=UTC)
    await service.list(bag_id="b1", since=since, rating_min=4)

    mock_repo.list.assert_awaited_once_with(bag_id="b1", profile_id=None, since=since, rating_min=4, limit=100)


async def test_update_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.update.return_value = False

    service = JournalService(repo=mock_repo)
    with pytest.raises(NotFoundError):
        await service.update("nope", rating=4, note_text=None)


async def test_update_passes_fields_to_repo() -> None:
    mock_repo = AsyncMock()
    mock_repo.update.return_value = True

    service = JournalService(repo=mock_repo)
    await service.update("e1", rating=4, note_text="Good")

    mock_repo.update.assert_awaited_once_with("e1", rating=4, note_text="Good")


async def test_delete_raises_not_found_when_missing() -> None:
    mock_repo = AsyncMock()
    mock_repo.delete.return_value = False

    service = JournalService(repo=mock_repo)
    with pytest.raises(NotFoundError):
        await service.delete("nope")


async def test_delete_succeeds_when_found() -> None:
    mock_repo = AsyncMock()
    mock_repo.delete.return_value = True

    service = JournalService(repo=mock_repo)
    await service.delete("e1")

    mock_repo.delete.assert_awaited_once_with("e1")
