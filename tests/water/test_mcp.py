import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from brew.errors import NotFoundError
from brew.water.mcp import register_water_mcp
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


async def test_get_water_wraps_domain_error_in_envelope(mcp: FastMCP, mock_service: AsyncMock) -> None:
    """Resource handler must surface DomainError as the standard envelope, not a raw transport error.

    The water service today has no NotFoundError-raising path, but the MCP wrapper must still
    forward any DomainError as the structured envelope so the wire contract stays consistent
    with bags / journal / aiden.
    """
    mock_service.get_water.side_effect = NotFoundError(
        message="Water snapshot missing",
        resource_kind="water",
        resource_id="current",
    )

    result = await mcp.read_resource("coffee://water")
    data = json.loads(result.contents[0].content)

    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert data["error"]["context"]["resource_id"] == "current"
