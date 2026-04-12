import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from brew.aiden.schedules.mcp import register_schedule_mcp
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
