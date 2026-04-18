import json
from unittest.mock import AsyncMock

import pytest
from brew.water.mcp import register_water_mcp
from fastmcp import FastMCP

from tests.water.conftest import make_water


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_water_mcp(server, mock_service)
    return server


async def test_coffee_water_resource_returns_json(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_water.return_value = make_water(remaining_ml=900)

    result = await mcp.read_resource("coffee://water")
    data = json.loads(result.contents[0].content)

    assert data["remaining_ml"] == 900
    assert "last_refilled_at" in data
