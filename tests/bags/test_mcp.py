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


async def test_create_bag_tool_creates_and_returns_bag(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create.return_value = make_bag(id="b1", name="Daybreak")

    result = await mcp.call_tool(
        "create_bag",
        {
            "name": "Daybreak",
            "origin": "Ethiopia",
            "roaster": "Intermission",
            "roast_level": "light",
            "initial_grams": 250,
            "profile_snapshot": {"ratio": 60.0},
            "profile_id": "p1",
        },
    )

    data = json.loads(result.content[0].text)
    assert data["status"] == "created"
    assert data["bag"]["id"] == "b1"
    assert data["bag"]["name"] == "Daybreak"
    mock_service.create.assert_awaited_once()


async def test_create_bag_tool_accepts_optional_roast_date(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create.return_value = make_bag(id="b1")

    result = await mcp.call_tool(
        "create_bag",
        {
            "name": "Daybreak",
            "origin": "Ethiopia",
            "roaster": "Intermission",
            "roast_level": "light",
            "initial_grams": 250,
            "profile_snapshot": {"ratio": 60.0},
            "roast_date": "2026-04-10",
        },
    )

    data = json.loads(result.content[0].text)
    assert data["status"] == "created"
    create_call = mock_service.create.await_args.args[0]
    assert create_call.roast_date.isoformat() == "2026-04-10"
