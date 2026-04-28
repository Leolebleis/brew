import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from brew.aiden.schedules.mcp import register_brew_now_mcp, register_schedule_mcp
from brew.aiden.schedules.model.brew_now import BrewNowResult
from brew.aiden.schedules.model.schedule import Schedule
from brew.errors import CloudUnreachableError, NotFoundError, ValidationError

_SAMPLE_SCHEDULE = Schedule(
    id="s1",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=500,
    profile_id="p1",
)


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_schedule_mcp(server, mock_service)
    return server


async def test_schedules_resource_returns_list(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.list_schedules.return_value = [_SAMPLE_SCHEDULE]
    result = await mcp.read_resource("coffee://schedules")
    data = json.loads(result.contents[0].content)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "s1"
    assert data[0]["profile_id"] == "p1"
    assert data[0]["amount_of_water"] == 500


async def test_schedules_resource_returns_error_on_cloud_error(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.list_schedules.side_effect = CloudUnreachableError(
        message="Fellow cloud unavailable", original="ConnectionError"
    )
    result = await mcp.read_resource("coffee://schedules")
    data = json.loads(result.contents[0].content)
    assert "error" in data
    assert data["error"]["code"] == "cloud_unreachable"


async def test_create_schedule_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_schedule.return_value = _SAMPLE_SCHEDULE
    result = await mcp.call_tool(
        "create_schedule",
        {
            "days": [False, True, True, True, True, True, False],
            "time_seconds": 25200,
            "water_ml": 500,
            "profile_id": "p1",
        },
    )
    data = json.loads(result.content[0].text)
    assert data["status"] == "created"
    assert data["schedule"]["id"] == "s1"


async def test_create_schedule_raises_tool_error_on_domain_error(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_schedule.side_effect = ValidationError(
        message="Fellow library rejected schedule", reason="library returned False"
    )
    with pytest.raises(ToolError) as exc_info:
        await mcp.call_tool(
            "create_schedule",
            {
                "days": [False, True, True, True, True, True, False],
                "time_seconds": 25200,
                "water_ml": 500,
                "profile_id": "bad-id",
            },
        )
    data = json.loads(str(exc_info.value))
    assert data["error"]["code"] == "validation"


async def test_update_schedule_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.update_schedule.return_value = None
    result = await mcp.call_tool(
        "update_schedule",
        {"schedule_id": "s1", "enabled": False},
    )
    assert "s1" in result.content[0].text
    assert "updated successfully" in result.content[0].text


async def test_update_schedule_raises_tool_error_on_validation_error(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.update_schedule.side_effect = ValidationError(
        message="Fellow API does not support updating: days",
        field="days",
        reason="Fellow library limitation",
    )
    with pytest.raises(ToolError) as exc_info:
        await mcp.call_tool(
            "update_schedule",
            {"schedule_id": "s1", "days": [True] * 7},
        )
    data = json.loads(str(exc_info.value))
    assert data["error"]["code"] == "validation"


async def test_delete_schedule_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.delete_schedule.return_value = None
    result = await mcp.call_tool("delete_schedule", {"schedule_id": "s1"})
    assert "s1" in result.content[0].text
    assert "deleted" in result.content[0].text


async def test_delete_schedule_raises_tool_error_on_not_found(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.delete_schedule.side_effect = NotFoundError(
        message="Schedule s1 not found", resource_kind="schedule", resource_id="s1"
    )
    with pytest.raises(ToolError) as exc_info:
        await mcp.call_tool("delete_schedule", {"schedule_id": "s1"})
    data = json.loads(str(exc_info.value))
    assert data["error"]["code"] == "not_found"


@pytest.fixture
def mock_brew_now_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp_with_brew_now(mock_brew_now_service: AsyncMock) -> FastMCP:
    mcp = FastMCP("test")
    register_brew_now_mcp(mcp, mock_brew_now_service)
    return mcp


SAMPLE_BREW_NOW = BrewNowResult(
    schedule_id="s6",
    profile_id="p3",
    water_ml=400,
    ready_at_seconds=53820,
    ready_at_local="14:57",
    ready_at_utc=datetime(2026, 4, 28, 13, 57, tzinfo=UTC),
    duration_estimate_seconds=360,
    device_timezone="Europe/London",
)


async def test_brew_now_tool_returns_envelope(mcp_with_brew_now: FastMCP, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.return_value = SAMPLE_BREW_NOW
    result = await mcp_with_brew_now.call_tool(
        "brew_now",
        {"profile_id": "p3", "water_ml": 400},
    )
    body = json.loads(result.content[0].text)
    assert body["status"] == "scheduled"
    assert body["result"]["schedule_id"] == "s6"
    assert body["result"]["ready_at_local"] == "14:57"


async def test_brew_now_tool_passes_extra_delay(mcp_with_brew_now: FastMCP, mock_brew_now_service: AsyncMock) -> None:
    mock_brew_now_service.brew_now.return_value = SAMPLE_BREW_NOW
    await mcp_with_brew_now.call_tool(
        "brew_now",
        {"profile_id": "p3", "water_ml": 400, "extra_delay_seconds": 90},
    )
    mock_brew_now_service.brew_now.assert_awaited_once_with(profile_id="p3", water_ml=400, extra_delay_seconds=90)


async def test_brew_now_tool_raises_tool_error_on_not_found(
    mcp_with_brew_now: FastMCP, mock_brew_now_service: AsyncMock
) -> None:
    from fastmcp.exceptions import ToolError  # noqa: PLC0415

    mock_brew_now_service.brew_now.side_effect = NotFoundError.for_resource("profile", "p99")
    with pytest.raises(ToolError) as exc_info:
        await mcp_with_brew_now.call_tool("brew_now", {"profile_id": "p99", "water_ml": 400})
    payload = json.loads(str(exc_info.value))
    assert payload["error"]["code"] == "not_found"


async def test_brew_now_tool_raises_tool_error_on_validation(
    mcp_with_brew_now: FastMCP, mock_brew_now_service: AsyncMock
) -> None:
    from fastmcp.exceptions import ToolError  # noqa: PLC0415

    mock_brew_now_service.brew_now.side_effect = ValidationError(
        message="incomplete", reason="profile_incomplete_for_mode"
    )
    with pytest.raises(ToolError) as exc_info:
        await mcp_with_brew_now.call_tool("brew_now", {"profile_id": "p3", "water_ml": 400})
    payload = json.loads(str(exc_info.value))
    assert payload["error"]["code"] == "validation"
