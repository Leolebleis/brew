from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.errors import NotFoundError
from brew.journal.dependencies import get_journal_service
from brew.main import app
from tests.journal.conftest import make_entry


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_service(mock_service: AsyncMock):
    app.dependency_overrides[get_journal_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(get_journal_service, None)


async def test_list_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = [make_entry(id="e1")]

    response = await client.get("/journal")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "e1"


async def test_list_passes_filters(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = []

    await client.get("/journal?bag_id=b1&rating_min=4&since=2026-04-01T00:00:00Z")

    call = mock_service.list.await_args
    assert call.kwargs["bag_id"] == "b1"
    assert call.kwargs["rating_min"] == 4
    assert call.kwargs["since"] == datetime(2026, 4, 1, 0, 0, 0, tzinfo=UTC)


async def test_get_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.get.return_value = make_entry(id="e1")

    response = await client.get("/journal/e1")

    assert response.status_code == 200
    assert response.json()["id"] == "e1"


async def test_get_returns_404_when_missing(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.get.side_effect = NotFoundError(message="not found", resource_kind="journal_entry", resource_id="e1")

    response = await client.get("/journal/e1")

    assert response.status_code == 404


async def test_patch_rating_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    response = await client.patch("/journal/e1", json={"rating": 4})

    assert response.status_code == 200
    mock_service.update.assert_awaited_once_with("e1", rating=4, note_text=None)


async def test_patch_note_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    response = await client.patch("/journal/e1", json={"note_text": "Caramel"})

    assert response.status_code == 200
    mock_service.update.assert_awaited_once_with("e1", rating=None, note_text="Caramel")


async def test_patch_rating_out_of_range_returns_422(client: AsyncClient) -> None:
    response = await client.patch("/journal/e1", json={"rating": 10})

    assert response.status_code == 422


async def test_patch_returns_404_when_missing(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.update.side_effect = NotFoundError(
        message="not found", resource_kind="journal_entry", resource_id="e1"
    )

    response = await client.patch("/journal/e1", json={"rating": 4})

    assert response.status_code == 404


async def test_delete_returns_204(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = None

    response = await client.delete("/journal/e1")

    assert response.status_code == 204
    mock_service.delete.assert_awaited_once_with("e1")
