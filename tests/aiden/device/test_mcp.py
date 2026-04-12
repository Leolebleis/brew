import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from brew.aiden.device.mcp import register_device_mcp
from brew.aiden.device.model.device import Device
from brew.errors import CloudUnreachableError


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_device_mcp(server, mock_service)
    return server


async def test_get_device_resource_returns_device_info(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_device.return_value = Device(brewer_id="b1", display_name="My Aiden", firmware_version="3.2.1")
    result = await mcp.read_resource("coffee://device")
    data = json.loads(result.contents[0].content)
    assert data["brewer_id"] == "b1"
    assert data["display_name"] == "My Aiden"
    assert data["firmware_version"] == "3.2.1"


async def test_get_device_resource_returns_error_json_when_unavailable(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.get_device.side_effect = CloudUnreachableError(
        message="Could not reach Fellow cloud", original="ConnectionError"
    )
    result = await mcp.read_resource("coffee://device")
    data = json.loads(result.contents[0].content)
    assert "error" in data


async def test_update_device_setting_returns_success_message(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.adjust_setting.return_value = None
    result = await mcp.call_tool("update_device_setting", {"setting": "volume", "value": 5})
    assert "volume" in result.content[0].text
    assert "updated successfully" in result.content[0].text


async def test_update_device_setting_raises_tool_error_when_unavailable(mcp: FastMCP, mock_service: AsyncMock) -> None:
    mock_service.adjust_setting.side_effect = CloudUnreachableError(
        message="Could not reach Fellow cloud", original="ConnectionError"
    )
    with pytest.raises(ToolError):
        await mcp.call_tool("update_device_setting", {"setting": "volume", "value": 5})
