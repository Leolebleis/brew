import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from brew.bags.mcp import register_bags_mcp
from tests.bags.conftest import make_bag


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_bags_mcp(server, mock_service)
    return server


async def test_coffee_bags_returns_list(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = [make_bag(id="b1"), make_bag(id="b2")]

    result = await mcp.read_resource("coffee://bags")
    data = json.loads(result.contents[0].content)

    assert len(data) == 2
    assert {b["id"] for b in data} == {"b1", "b2"}


async def test_coffee_bag_by_id_returns_one(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get.return_value = make_bag(id="b1", name="Daybreak")

    result = await mcp.read_resource("coffee://bags/b1")
    data = json.loads(result.contents[0].content)

    assert data["id"] == "b1"
    assert data["name"] == "Daybreak"


async def test_coffee_bags_active_returns_active_bag(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_active.return_value = make_bag(id="a1", is_active=True)

    result = await mcp.read_resource("coffee://bags/active")
    data = json.loads(result.contents[0].content)

    assert data["id"] == "a1"
    assert data["is_active"] is True


async def test_coffee_bags_active_returns_null_when_none(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_active.return_value = None

    result = await mcp.read_resource("coffee://bags/active")
    data = json.loads(result.contents[0].content)

    assert data is None
