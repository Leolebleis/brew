import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from brew.aiden.profiles.mcp import register_profile_mcp
from brew.aiden.profiles.model.profile import Profile, ProfileLink
from brew.aiden.profiles.service import (
    ProfileCreateOutcome,
    ProfileCreateResult,
    ProfileDeleteOutcome,
    ProfileDeleteResult,
    ProfileGetOutcome,
    ProfileGetResult,
    ProfileLinkOutcome,
    ProfileLinkResult,
    ProfileListOutcome,
    ProfileListResult,
    ProfileUpdateOutcome,
    ProfileUpdateResult,
)


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_profile_mcp(server, mock_service)
    return server


async def test_profiles_resource_returns_list(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.list_profiles.return_value = ProfileListResult(
        outcome=ProfileListOutcome.SUCCESS,
        profiles=[
            Profile(id="p1", title="Morning Brew", ratio=16.0),
            Profile(id="p2", title="Afternoon Brew", ratio=15.0),
        ],
    )
    result = await mcp.read_resource("coffee://profiles")
    data = json.loads(result.contents[0].content)
    assert len(data) == 2
    assert data[0]["id"] == "p1"
    assert data[0]["title"] == "Morning Brew"
    assert data[1]["id"] == "p2"


async def test_profile_by_id_resource(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.SUCCESS,
        profile=Profile(id="p1", title="Morning Brew", ratio=16.0),
    )
    result = await mcp.read_resource("coffee://profiles/p1")
    data = json.loads(result.contents[0].content)
    assert data["id"] == "p1"
    assert data["title"] == "Morning Brew"
    mock_service.get_profile.assert_called_once_with("p1")


async def test_profile_by_id_not_found(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.NOT_FOUND,
        error="Profile p99 not found",
    )
    result = await mcp.read_resource("coffee://profiles/p99")
    data = json.loads(result.contents[0].content)
    assert "error" in data
    assert "p99" in data["error"]


async def test_create_profile_from_link(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_profile_from_link.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=Profile(id="p3", title="Imported Profile"),
    )
    result = await mcp.call_tool("create_profile", {"brew_link_url": "https://fellow.app/p/abc123"})
    data = json.loads(result.content[0].text)
    assert data["status"] == "created"
    assert data["profile"]["id"] == "p3"
    mock_service.create_profile_from_link.assert_called_once_with("https://fellow.app/p/abc123")


async def test_create_profile_from_fields(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_profile.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=Profile(id="p4", title="Manual Profile", ratio=15.5),
    )
    result = await mcp.call_tool(
        "create_profile",
        {
            "title": "Manual Profile",
            "profile_type": 1,
            "ratio": 15.5,
        },
    )
    data = json.loads(result.content[0].text)
    assert data["status"] == "created"
    assert data["profile"]["title"] == "Manual Profile"
    mock_service.create_profile.assert_called_once()


async def test_update_profile_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.update_profile.return_value = ProfileUpdateResult(outcome=ProfileUpdateOutcome.SUCCESS)
    result = await mcp.call_tool("update_profile", {"profile_id": "p1", "ratio": 17.0})
    assert "p1" in result.content[0].text
    assert "updated successfully" in result.content[0].text
    mock_service.update_profile.assert_called_once()


async def test_delete_profile_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.delete_profile.return_value = ProfileDeleteResult(outcome=ProfileDeleteOutcome.SUCCESS)
    result = await mcp.call_tool("delete_profile", {"profile_id": "p1"})
    assert "p1" in result.content[0].text
    assert "deleted" in result.content[0].text
    mock_service.delete_profile.assert_called_once_with("p1")


async def test_delete_profile_unavailable(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.delete_profile.return_value = ProfileDeleteResult(
        outcome=ProfileDeleteOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    with pytest.raises(ToolError):
        await mcp.call_tool("delete_profile", {"profile_id": "p1"})


async def test_generate_profile_link_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.generate_link.return_value = ProfileLinkResult(
        outcome=ProfileLinkOutcome.SUCCESS,
        link=ProfileLink(url="https://fellow.app/p/abc123"),
    )
    result = await mcp.call_tool("generate_profile_link", {"profile_id": "p1"})
    data = json.loads(result.content[0].text)
    assert data["profile_id"] == "p1"
    assert data["share_url"] == "https://fellow.app/p/abc123"
    mock_service.generate_link.assert_called_once_with("p1")
