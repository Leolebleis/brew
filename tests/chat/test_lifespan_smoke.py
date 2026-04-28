"""Smoke test: chat agent + service are wired into app.dependency_overrides when enabled.

Approach: monkeypatch `brew.main._chat_enabled`, `brew.main._mcp_enabled`, and
`brew.main._mcp_server` directly (Option A from the plan), then call `_app_lifespan`
directly — skipping the outer `lifespan` wrapper which would try to spin up
`_mcp_app.lifespan(app)`. This is sufficient because the test's only goal is to
verify that `get_chat_service` ends up in `app.dependency_overrides`.

`build_fellow_client` is patched in both modules it's referenced from (same pattern
as `tests/e2e/conftest.py`) so no network calls are made. No actual Anthropic API
calls occur because the agent is constructed but never invoked.
"""

from unittest.mock import Mock

import pytest
from fastmcp import FastMCP
from fellow_aiden import FellowAiden

import brew.main
from brew.aiden.dependencies import get_aiden_settings
from brew.chat.dependencies import get_chat_service
from brew.dependencies import get_settings
from brew.main import _app_lifespan, app


def _make_fellow_mock() -> Mock:
    fellow = Mock(spec=FellowAiden)
    fellow.get_device_config.return_value = {
        "id": "brewer-test-id",
        "displayName": "Test Aiden",
        "firmwareVersion": "3.0.0",
        "serialNumber": "SN-TEST",
        "sku": "AIDEN",
        "isConnected": True,
        "deviceTimezone": "UTC",
        "totalWaterVolumeL": 0,
        "brewing": False,
        "missingWater": False,
        "carafePresent": True,
        "lidClosed": True,
        "batchBrewBasketPresent": True,
    }
    return fellow


async def test_chat_wired_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """app.dependency_overrides[get_chat_service] is set after _app_lifespan starts."""
    # Set the Anthropic API key before ChatSettings is constructed
    monkeypatch.setenv("FELLOW_ANTHROPIC_API_KEY", "sk-ant-test")

    # Patch module-level flags and provide a real FastMCP instance for _mcp_server
    monkeypatch.setattr(brew.main, "_chat_enabled", True)
    monkeypatch.setattr(brew.main, "_mcp_enabled", True)
    monkeypatch.setattr(brew.main, "_mcp_server", FastMCP("test-mcp"), raising=False)

    # Mock Fellow client so no network calls are made
    fellow_mock = _make_fellow_mock()
    monkeypatch.setattr("brew.aiden.dependencies.build_fellow_client", lambda: fellow_mock)
    monkeypatch.setattr("brew.main.build_fellow_client", lambda: fellow_mock)

    # Clear caches so env overrides are picked up fresh
    get_settings.cache_clear()
    get_aiden_settings.cache_clear()

    async with _app_lifespan(app):
        assert get_chat_service in app.dependency_overrides, (
            "get_chat_service should be in dependency_overrides when chat + MCP are enabled"
        )
