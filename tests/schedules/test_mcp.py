import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from fellow_aiden_api.schedules.mcp import register_schedule_mcp
from fellow_aiden_api.schedules.model.schedule import Schedule
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleCreateResult,
    ScheduleDeleteOutcome,
    ScheduleDeleteResult,
    ScheduleListOutcome,
    ScheduleListResult,
    ScheduleUpdateOutcome,
    ScheduleUpdateResult,
)

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
    mock_service.list_schedules.return_value = ScheduleListResult(
        outcome=ScheduleListOutcome.SUCCESS,
        schedules=[_SAMPLE_SCHEDULE],
    )
    result = await mcp.read_resource("coffee://schedules")
    data = json.loads(result.contents[0].content)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "s1"
    assert data[0]["profile_id"] == "p1"
    assert data[0]["amount_of_water"] == 500


async def test_create_schedule_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=_SAMPLE_SCHEDULE,
    )
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


async def test_create_schedule_unavailable(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    with pytest.raises(ToolError):
        await mcp.call_tool(
            "create_schedule",
            {
                "days": [False, True, True, True, True, True, False],
                "time_seconds": 25200,
                "water_ml": 500,
                "profile_id": "p1",
            },
        )


async def test_update_schedule_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.update_schedule.return_value = ScheduleUpdateResult(
        outcome=ScheduleUpdateOutcome.SUCCESS,
    )
    result = await mcp.call_tool(
        "update_schedule",
        {"schedule_id": "s1", "water_ml": 400},
    )
    assert "s1" in result.content[0].text
    assert "updated successfully" in result.content[0].text


async def test_delete_schedule_success(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.delete_schedule.return_value = ScheduleDeleteResult(
        outcome=ScheduleDeleteOutcome.SUCCESS,
    )
    result = await mcp.call_tool("delete_schedule", {"schedule_id": "s1"})
    assert "s1" in result.content[0].text
    assert "deleted" in result.content[0].text


async def test_brew_now_creates_schedule_and_returns_immediately(mcp: FastMCP, mock_service: AsyncMock) -> None:
    created_schedule = Schedule(
        id="s-temp",
        days=[False] * 7,
        second_from_start_of_day=0,
        enabled=True,
        amount_of_water=500,
        profile_id="p1",
    )
    mock_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=created_schedule,
    )

    result = await mcp.call_tool("brew_now", {"profile_id": "p1", "water_ml": 500})

    text = result.content[0].text
    assert "s-temp" in text
    mock_service.create_schedule.assert_called_once()


async def test_brew_now_fails_when_creation_fails(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )

    with pytest.raises(ToolError):
        await mcp.call_tool("brew_now", {"profile_id": "p1", "water_ml": 500})
