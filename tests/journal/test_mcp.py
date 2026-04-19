import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from brew.errors import NotFoundError
from brew.journal.mcp import register_journal_mcp
from tests.journal.conftest import make_entry


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_journal_mcp(server, mock_service)
    return server


async def test_coffee_journal_returns_list(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.list.return_value = [make_entry(id="e1"), make_entry(id="e2")]

    result = await mcp.read_resource("coffee://journal")
    data = json.loads(result.contents[0].content)

    assert len(data) == 2
    assert {e["id"] for e in data} == {"e1", "e2"}


async def test_coffee_journal_by_id_returns_one(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get.return_value = make_entry(id="e1", rating=5)

    result = await mcp.read_resource("coffee://journal/e1")
    data = json.loads(result.contents[0].content)

    assert data["id"] == "e1"
    assert data["rating"] == 5


async def test_coffee_journal_list_is_bounded(mcp: FastMCP, mock_service: AsyncMock) -> None:
    """The flat resource caps at a reasonable default. Detailed filters live in the chat-backend tool."""
    mock_service.list.return_value = []

    await mcp.read_resource("coffee://journal")

    mock_service.list.assert_awaited_once()
    call = mock_service.list.await_args
    assert call.kwargs.get("limit") == 50


async def test_get_entry_wraps_not_found_in_envelope(mcp: FastMCP, mock_service: AsyncMock) -> None:
    """Resource handler must surface NotFoundError as the standard envelope, not a raw transport error."""
    mock_service.get.side_effect = NotFoundError(
        message="Journal entry e99 not found",
        resource_kind="journal_entry",
        resource_id="e99",
    )

    result = await mcp.read_resource("coffee://journal/e99")
    data = json.loads(result.contents[0].content)

    assert "error" in data
    assert data["error"]["code"] == "not_found"
    assert data["error"]["context"]["resource_id"] == "e99"
