from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.bags.dependencies import get_bag_service
from brew.bags.model.bag import BagUpdate
from brew.errors import NotFoundError
from brew.main import app
from tests.bags.conftest import make_bag


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_service(mock_service: AsyncMock):
    app.dependency_overrides[get_bag_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(get_bag_service, None)


async def test_list_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = [make_bag(id="b1")]

    response = await client.get("/api/bags")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "b1"


async def test_list_passes_filters(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = []

    await client.get("/api/bags?active=true&roaster=Onyx")

    mock_service.list.assert_awaited_once_with(active=True, finished=None, roaster="Onyx", origin=None)


async def test_get_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.get.return_value = make_bag(id="b1")

    response = await client.get("/api/bags/b1")

    assert response.status_code == 200
    assert response.json()["id"] == "b1"


async def test_get_returns_404_when_missing(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.get.side_effect = NotFoundError(message="Bag b1 not found", resource_kind="bag", resource_id="b1")

    response = await client.get("/api/bags/b1")

    assert response.status_code == 404


async def test_create_returns_201(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.create.return_value = make_bag(id="b1")

    payload = {
        "name": "Daybreak",
        "origin": "Ethiopia",
        "roaster": "Intermission",
        "roast_level": "light",
        "initial_grams": 250,
        "profile_snapshot": {"ratio": 60.0},
    }
    response = await client.post("/api/bags", json=payload)

    assert response.status_code == 201
    assert response.json()["id"] == "b1"


async def test_patch_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.update.return_value = None

    response = await client.patch("/api/bags/b1", json={"name": "Renamed"})

    assert response.status_code == 200
    mock_service.update.assert_awaited_once()
    args = mock_service.update.await_args
    assert args.args[0] == "b1"
    assert isinstance(args.args[1], BagUpdate)
    assert args.args[1].name == "Renamed"


async def test_patch_returns_404_when_missing(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.update.side_effect = NotFoundError(message="not found", resource_kind="bag", resource_id="b1")

    response = await client.patch("/api/bags/b1", json={"name": "X"})

    assert response.status_code == 404


async def test_delete_returns_204(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.delete.return_value = None

    response = await client.delete("/api/bags/b1")

    assert response.status_code == 204
    mock_service.delete.assert_awaited_once_with("b1")


async def test_activate_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.activate.return_value = None

    response = await client.post("/api/bags/b1/activate")

    assert response.status_code == 200
    mock_service.activate.assert_awaited_once_with("b1")


async def test_zero_returns_200(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.zero.return_value = None

    response = await client.post("/api/bags/b1/zero")

    assert response.status_code == 200
    mock_service.zero.assert_awaited_once_with("b1")
