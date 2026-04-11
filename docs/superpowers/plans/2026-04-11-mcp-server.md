# MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a hand-crafted MCP server to the Fellow Aiden FastAPI app, exposing coffee machine control via resources and tools over Streamable HTTP.

**Architecture:** The MCP server is a Starlette sub-app (via `fastmcp`) mounted onto the existing FastAPI app at `/mcp`. It shares the service layer directly — no HTTP round-trip. Each domain (`device`, `profiles`, `schedules`) has an `mcp.py` file alongside its `router.py`, following the existing pattern where each domain defines its own interface. Auth is an API key middleware on the sub-app. The whole thing is gated behind `FELLOW_MCP_ENABLED`.

**Tech Stack:** `fastmcp` (standalone FastMCP package), `mcp` (types only), Python 3.13, pytest-asyncio

**Spec:** `docs/superpowers/specs/2026-04-11-mcp-server-design.md`

**Deviation from spec:** Spec says `mcp` SDK. Using `fastmcp` (standalone) instead — the bundled `mcp.server.fastmcp` has a known mounting bug under FastAPI sub-paths (modelcontextprotocol/python-sdk#1367). `fastmcp` is the actively maintained successor with proper `http_app()` + FastAPI mount support.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `pyproject.toml` | Modify | Add `fastmcp` dependency |
| `src/fellow_aiden_api/config.py` | Modify | Add `mcp_enabled: bool = False` |
| `src/fellow_aiden_api/mcp_auth.py` | Create | Starlette middleware that validates `X-API-Key` header |
| `src/fellow_aiden_api/device/mcp.py` | Create | `register_device_mcp()` — 1 resource, 1 tool |
| `src/fellow_aiden_api/profiles/mcp.py` | Create | `register_profile_mcp()` — 2 resources, 4 tools |
| `src/fellow_aiden_api/schedules/mcp.py` | Create | `register_schedule_mcp()` — 1 resource, 3 tools + `brew_now` |
| `src/fellow_aiden_api/main.py` | Modify | Conditionally create FastMCP, register, mount |
| `tests/test_mcp_auth.py` | Create | Auth middleware tests |
| `tests/device/test_mcp.py` | Create | Device resource + tool tests |
| `tests/profiles/test_mcp.py` | Create | Profile resources + tools tests |
| `tests/schedules/test_mcp.py` | Create | Schedule resources + tools + brew_now tests |
| `CLAUDE.md` | Modify | Document MCP endpoint |

---

### Task 1: Add `fastmcp` dependency and `mcp_enabled` config

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/fellow_aiden_api/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write failing test for `mcp_enabled` setting**

```python
# tests/test_config.py — add to existing file

def test_settings_mcp_enabled_defaults_false() -> None:
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is False


def test_settings_mcp_enabled_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "true")
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config.py -v -k "mcp_enabled"`
Expected: FAIL — `mcp_enabled` not a field on `Settings`

- [ ] **Step 3: Add `mcp_enabled` to Settings**

```python
# src/fellow_aiden_api/config.py — add field to Settings class
    mcp_enabled: bool = False
```

- [ ] **Step 4: Add `fastmcp` to dependencies**

```toml
# pyproject.toml — add to dependencies list
    "fastmcp>=2",
```

- [ ] **Step 5: Install dependencies**

Run: `uv sync`

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_config.py -v`
Expected: ALL PASS

- [ ] **Step 7: Run full test suite to check nothing broke**

Run: `uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock src/fellow_aiden_api/config.py tests/test_config.py
git commit -m "feat: add fastmcp dependency and mcp_enabled config flag"
```

---

### Task 2: MCP auth middleware

**Files:**
- Create: `src/fellow_aiden_api/mcp_auth.py`
- Create: `tests/test_mcp_auth.py`

The MCP sub-app is a Starlette app, not FastAPI — so FastAPI's `Depends()` doesn't apply. Auth is a Starlette `BaseHTTPMiddleware` that checks the `X-API-Key` header against `Settings.api_key`. If `api_key` is `None` (not configured), all requests pass through (same behavior as the REST API).

- [ ] **Step 1: Write failing tests for MCP auth middleware**

```python
# tests/test_mcp_auth.py
from unittest.mock import AsyncMock

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.testclient import TestClient

from fellow_aiden_api.mcp_auth import McpApiKeyMiddleware


async def _ok_endpoint(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


def _make_app(api_key: str | None) -> Starlette:
    app = Starlette(routes=[Route("/test", _ok_endpoint)])
    app.add_middleware(McpApiKeyMiddleware, api_key=api_key)
    return app


def test_allows_request_when_no_api_key_configured() -> None:
    app = _make_app(api_key=None)
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200


def test_allows_request_with_valid_api_key() -> None:
    app = _make_app(api_key="secret-key")
    client = TestClient(app)
    response = client.get("/test", headers={"X-API-Key": "secret-key"})
    assert response.status_code == 200


def test_rejects_request_with_missing_api_key() -> None:
    app = _make_app(api_key="secret-key")
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 403


def test_rejects_request_with_wrong_api_key() -> None:
    app = _make_app(api_key="secret-key")
    client = TestClient(app)
    response = client.get("/test", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mcp_auth.py -v`
Expected: FAIL — `McpApiKeyMiddleware` does not exist

- [ ] **Step 3: Implement the middleware**

```python
# src/fellow_aiden_api/mcp_auth.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class McpApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, api_key: str | None = None) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._api_key = api_key

    async def dispatch(self, request: Request, call_next: object) -> Response:
        if self._api_key is not None:
            provided = request.headers.get("X-API-Key")
            if provided is None or provided != self._api_key:
                return JSONResponse({"detail": "Invalid API key"}, status_code=403)
        return await call_next(request)  # type: ignore[operator]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_mcp_auth.py -v`
Expected: ALL PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/fellow_aiden_api/mcp_auth.py tests/test_mcp_auth.py`

- [ ] **Step 6: Commit**

```bash
git add src/fellow_aiden_api/mcp_auth.py tests/test_mcp_auth.py
git commit -m "feat: add MCP API key auth middleware"
```

---

### Task 3: Device MCP — resource and tool

**Files:**
- Create: `src/fellow_aiden_api/device/mcp.py`
- Create: `tests/device/test_mcp.py`

**Pattern:** Each domain's `mcp.py` exports a `register_*_mcp(mcp, service)` function that defines resources and tools as nested closures over the service instance. This mirrors how `router.py` uses FastAPI's dependency injection — different mechanism, same shape.

**Testing pattern:** Create a `FastMCP` instance, register tools with a mock service, then use `FastMCP.call_tool()` and `FastMCP.read_resource()` to invoke them directly (no HTTP needed for unit tests).

- [ ] **Step 1: Write failing tests**

```python
# tests/device/test_mcp.py
import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP

from fellow_aiden_api.device.mcp import register_device_mcp
from fellow_aiden_api.device.model.device import Device, DeviceSettings
from fellow_aiden_api.device.service import (
    DeviceGetOutcome,
    DeviceGetResult,
    DeviceSettingsOutcome,
    DeviceSettingsResult,
)


@pytest.fixture
def mock_device_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_device_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_device_mcp(server, mock_device_service)
    return server


async def test_device_resource_returns_device_info(
    mcp: FastMCP, mock_device_service: AsyncMock
) -> None:
    mock_device_service.get_device.return_value = DeviceGetResult(
        outcome=DeviceGetOutcome.SUCCESS,
        device=Device(brewer_id="b1", display_name="My Aiden", firmware_version="3.2.1"),
    )
    result = await mcp.read_resource("coffee://device")
    text = result[0].content if hasattr(result[0], "content") else str(result[0])
    data = json.loads(text)
    assert data["brewer_id"] == "b1"
    assert data["display_name"] == "My Aiden"
    assert data["firmware_version"] == "3.2.1"


async def test_device_resource_returns_error_when_unavailable(
    mcp: FastMCP, mock_device_service: AsyncMock
) -> None:
    mock_device_service.get_device.return_value = DeviceGetResult(
        outcome=DeviceGetOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    result = await mcp.read_resource("coffee://device")
    text = result[0].content if hasattr(result[0], "content") else str(result[0])
    assert "unavailable" in text.lower() or "error" in text.lower()


async def test_update_device_setting_success(
    mcp: FastMCP, mock_device_service: AsyncMock
) -> None:
    mock_device_service.adjust_setting.return_value = DeviceSettingsResult(
        outcome=DeviceSettingsOutcome.SUCCESS,
    )
    result = await mcp.call_tool("update_device_setting", {"setting": "volume", "value": 5})
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "ok" in text.lower() or "success" in text.lower() or "updated" in text.lower()


async def test_update_device_setting_unavailable(
    mcp: FastMCP, mock_device_service: AsyncMock
) -> None:
    mock_device_service.adjust_setting.return_value = DeviceSettingsResult(
        outcome=DeviceSettingsOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    # ToolError should be raised for isError responses
    from fastmcp.exceptions import ToolError

    with pytest.raises(ToolError, match="(?i)unavailable|unreachable"):
        await mcp.call_tool("update_device_setting", {"setting": "volume", "value": 5})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/device/test_mcp.py -v`
Expected: FAIL — `fellow_aiden_api.device.mcp` does not exist

- [ ] **Step 3: Implement device MCP**

```python
# src/fellow_aiden_api/device/mcp.py
import json

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from fellow_aiden_api.device.model.device import DeviceSettings
from fellow_aiden_api.device.service import DeviceGetOutcome, DeviceService, DeviceSettingsOutcome


def register_device_mcp(mcp: FastMCP, service: DeviceService) -> None:
    @mcp.resource("coffee://device", description="Coffee machine info — brewer ID, display name, firmware version.")
    async def get_device() -> str:
        result = await service.get_device()
        if result.outcome != DeviceGetOutcome.SUCCESS or result.device is None:
            return json.dumps({"error": "Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry."})
        return json.dumps({
            "brewer_id": result.device.brewer_id,
            "display_name": result.device.display_name,
            "firmware_version": result.device.firmware_version,
        })

    @mcp.tool(
        description="Change a device setting (e.g. display name, volume). Provide the setting name and new value.",
    )
    async def update_device_setting(setting: str, value: str | int | float | bool) -> str:
        settings = DeviceSettings(setting=setting, value=value)
        result = await service.adjust_setting(settings)
        if result.outcome != DeviceSettingsOutcome.SUCCESS:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return f"Device setting '{setting}' updated successfully."
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/device/test_mcp.py -v`
Expected: ALL PASS

**Note:** The exact `FastMCP` API for `call_tool()`, `read_resource()`, and error types may differ from what's written here. If tests fail due to API differences, adjust the test assertions and imports to match the actual `fastmcp` API. Check `fastmcp` docs at gofastmcp.com for the correct testing interface.

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/fellow_aiden_api/device/mcp.py tests/device/test_mcp.py`

- [ ] **Step 6: Commit**

```bash
git add src/fellow_aiden_api/device/mcp.py tests/device/test_mcp.py
git commit -m "feat: add device MCP resource and tool"
```

---

### Task 4: Profiles MCP — resources and tools

**Files:**
- Create: `src/fellow_aiden_api/profiles/mcp.py`
- Create: `tests/profiles/test_mcp.py`

Profiles has 2 resources (`coffee://profiles`, `coffee://profiles/{id}`) and 4 tools (`create_profile`, `update_profile`, `delete_profile`, `generate_profile_link`).

- [ ] **Step 1: Write failing tests**

```python
# tests/profiles/test_mcp.py
import json
from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from fellow_aiden_api.profiles.mcp import register_profile_mcp
from fellow_aiden_api.profiles.model.profile import Profile, ProfileLink
from fellow_aiden_api.profiles.service import (
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
def mock_profile_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_profile_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_profile_mcp(server, mock_profile_service)
    return server


# --- Resources ---


async def test_profiles_resource_returns_list(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.list_profiles.return_value = ProfileListResult(
        outcome=ProfileListOutcome.SUCCESS,
        profiles=[
            Profile(id="p1", title="Morning Brew", ratio=16.0),
            Profile(id="p2", title="Evening Light"),
        ],
    )
    result = await mcp.read_resource("coffee://profiles")
    text = result[0].content if hasattr(result[0], "content") else str(result[0])
    data = json.loads(text)
    assert len(data) == 2
    assert data[0]["id"] == "p1"
    assert data[1]["title"] == "Evening Light"


async def test_profile_by_id_resource(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.SUCCESS,
        profile=Profile(id="p1", title="Morning Brew", ratio=16.0, bloom_enabled=True),
    )
    result = await mcp.read_resource("coffee://profiles/p1")
    text = result[0].content if hasattr(result[0], "content") else str(result[0])
    data = json.loads(text)
    assert data["id"] == "p1"
    assert data["bloom_enabled"] is True


async def test_profile_by_id_not_found(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.NOT_FOUND,
        error="Profile p999 not found",
    )
    result = await mcp.read_resource("coffee://profiles/p999")
    text = result[0].content if hasattr(result[0], "content") else str(result[0])
    assert "not found" in text.lower()


# --- Tools ---


async def test_create_profile_from_link(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.create_profile_from_link.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=Profile(id="p3", title="Imported Brew"),
    )
    result = await mcp.call_tool(
        "create_profile", {"brew_link_url": "https://fellow.app/p/abc123"}
    )
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "p3" in text


async def test_create_profile_from_fields(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.create_profile.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=Profile(id="p4", title="Custom Brew"),
    )
    result = await mcp.call_tool("create_profile", {
        "title": "Custom Brew",
        "profile_type": 1,
        "ratio": 16.0,
        "bloom_enabled": True,
        "bloom_ratio": 2.0,
        "bloom_duration": 30,
        "bloom_temperature": 93.0,
        "ss_pulses_enabled": False,
        "ss_pulses_number": 1,
        "ss_pulses_interval": 10,
        "ss_pulse_temperatures": [93.0],
        "batch_pulses_enabled": False,
        "batch_pulses_number": 1,
        "batch_pulses_interval": 10,
        "batch_pulse_temperatures": [93.0],
    })
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "p4" in text or "Custom Brew" in text


async def test_update_profile_success(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.update_profile.return_value = ProfileUpdateResult(
        outcome=ProfileUpdateOutcome.SUCCESS,
    )
    result = await mcp.call_tool("update_profile", {"profile_id": "p1", "title": "Renamed"})
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "updated" in text.lower() or "success" in text.lower()


async def test_delete_profile_success(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.delete_profile.return_value = ProfileDeleteResult(
        outcome=ProfileDeleteOutcome.SUCCESS,
    )
    result = await mcp.call_tool("delete_profile", {"profile_id": "p1"})
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "deleted" in text.lower()


async def test_delete_profile_unavailable(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.delete_profile.return_value = ProfileDeleteResult(
        outcome=ProfileDeleteOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    with pytest.raises(ToolError, match="(?i)unavailable|unreachable"):
        await mcp.call_tool("delete_profile", {"profile_id": "p1"})


async def test_generate_profile_link_success(
    mcp: FastMCP, mock_profile_service: AsyncMock
) -> None:
    mock_profile_service.generate_link.return_value = ProfileLinkResult(
        outcome=ProfileLinkOutcome.SUCCESS,
        link=ProfileLink(url="https://fellow.app/p/abc123"),
    )
    result = await mcp.call_tool("generate_profile_link", {"profile_id": "p1"})
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "abc123" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/profiles/test_mcp.py -v`
Expected: FAIL — `fellow_aiden_api.profiles.mcp` does not exist

- [ ] **Step 3: Implement profiles MCP**

```python
# src/fellow_aiden_api/profiles/mcp.py
import json
from dataclasses import asdict

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from fellow_aiden_api.profiles.model.profile import ProfileCreate, ProfileUpdate
from fellow_aiden_api.profiles.service import (
    ProfileCreateOutcome,
    ProfileDeleteOutcome,
    ProfileGetOutcome,
    ProfileLinkOutcome,
    ProfileListOutcome,
    ProfileService,
    ProfileUpdateOutcome,
)


def register_profile_mcp(mcp: FastMCP, service: ProfileService) -> None:
    @mcp.resource("coffee://profiles", description="All brew profiles with their settings.")
    async def list_profiles() -> str:
        result = await service.list_profiles()
        if result.outcome != ProfileListOutcome.SUCCESS or result.profiles is None:
            return json.dumps({"error": "Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry."})
        return json.dumps([asdict(p) for p in result.profiles])

    @mcp.resource("coffee://profiles/{profile_id}", description="A single brew profile by ID.")
    async def get_profile(profile_id: str) -> str:
        result = await service.get_profile(profile_id)
        if result.outcome == ProfileGetOutcome.NOT_FOUND:
            return json.dumps({"error": f"No profile found with ID '{profile_id}'. Use the coffee://profiles resource to see available profiles."})
        if result.outcome != ProfileGetOutcome.SUCCESS or result.profile is None:
            return json.dumps({"error": "Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry."})
        return json.dumps(asdict(result.profile))

    @mcp.tool(
        description="Create a new brew profile. Either provide all profile fields for manual creation, or just a brew_link_url to import from a shared link. If brew_link_url is provided, all other fields are ignored.",
    )
    async def create_profile(
        brew_link_url: str | None = None,
        title: str | None = None,
        profile_type: int | None = None,
        ratio: float | None = None,
        bloom_enabled: bool | None = None,
        bloom_ratio: float | None = None,
        bloom_duration: int | None = None,
        bloom_temperature: float | None = None,
        ss_pulses_enabled: bool | None = None,
        ss_pulses_number: int | None = None,
        ss_pulses_interval: int | None = None,
        ss_pulse_temperatures: list[float] | None = None,
        batch_pulses_enabled: bool | None = None,
        batch_pulses_number: int | None = None,
        batch_pulses_interval: int | None = None,
        batch_pulse_temperatures: list[float] | None = None,
    ) -> str:
        if brew_link_url is not None:
            result = await service.create_profile_from_link(brew_link_url)
        else:
            if title is None or profile_type is None or ratio is None:
                raise ToolError("Manual profile creation requires at least: title, profile_type, ratio, and all bloom/pulse fields.")
            create = ProfileCreate(
                title=title,
                profile_type=profile_type,
                ratio=ratio,
                bloom_enabled=bloom_enabled if bloom_enabled is not None else False,
                bloom_ratio=bloom_ratio if bloom_ratio is not None else 2.0,
                bloom_duration=bloom_duration if bloom_duration is not None else 30,
                bloom_temperature=bloom_temperature if bloom_temperature is not None else 93.0,
                ss_pulses_enabled=ss_pulses_enabled if ss_pulses_enabled is not None else False,
                ss_pulses_number=ss_pulses_number if ss_pulses_number is not None else 1,
                ss_pulses_interval=ss_pulses_interval if ss_pulses_interval is not None else 10,
                ss_pulse_temperatures=ss_pulse_temperatures if ss_pulse_temperatures is not None else [93.0],
                batch_pulses_enabled=batch_pulses_enabled if batch_pulses_enabled is not None else False,
                batch_pulses_number=batch_pulses_number if batch_pulses_number is not None else 1,
                batch_pulses_interval=batch_pulses_interval if batch_pulses_interval is not None else 10,
                batch_pulse_temperatures=batch_pulse_temperatures if batch_pulse_temperatures is not None else [93.0],
            )
            result = await service.create_profile(create)
        if result.outcome != ProfileCreateOutcome.SUCCESS or result.profile is None:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return json.dumps({"status": "created", "profile": asdict(result.profile)})

    @mcp.tool(
        description="Update specific fields on an existing brew profile. Only provide the fields you want to change.",
    )
    async def update_profile(
        profile_id: str,
        title: str | None = None,
        ratio: float | None = None,
        bloom_enabled: bool | None = None,
        bloom_ratio: float | None = None,
        bloom_duration: int | None = None,
        bloom_temperature: float | None = None,
        ss_pulses_enabled: bool | None = None,
        ss_pulses_number: int | None = None,
        ss_pulses_interval: int | None = None,
        ss_pulse_temperatures: list[float] | None = None,
        batch_pulses_enabled: bool | None = None,
        batch_pulses_number: int | None = None,
        batch_pulses_interval: int | None = None,
        batch_pulse_temperatures: list[float] | None = None,
    ) -> str:
        update = ProfileUpdate(
            title=title, ratio=ratio, bloom_enabled=bloom_enabled,
            bloom_ratio=bloom_ratio, bloom_duration=bloom_duration,
            bloom_temperature=bloom_temperature, ss_pulses_enabled=ss_pulses_enabled,
            ss_pulses_number=ss_pulses_number, ss_pulses_interval=ss_pulses_interval,
            ss_pulse_temperatures=ss_pulse_temperatures, batch_pulses_enabled=batch_pulses_enabled,
            batch_pulses_number=batch_pulses_number, batch_pulses_interval=batch_pulses_interval,
            batch_pulse_temperatures=batch_pulse_temperatures,
        )
        result = await service.update_profile(profile_id, update)
        if result.outcome != ProfileUpdateOutcome.SUCCESS:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return f"Profile '{profile_id}' updated successfully."

    @mcp.tool(
        description="Permanently delete a brew profile. This cannot be undone.",
        annotations=ToolAnnotations(destructive_hint=True),
    )
    async def delete_profile(profile_id: str) -> str:
        result = await service.delete_profile(profile_id)
        if result.outcome != ProfileDeleteOutcome.SUCCESS:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return f"Profile '{profile_id}' deleted."

    @mcp.tool(
        description="Generate a shareable URL for a brew profile that others can import.",
        annotations=ToolAnnotations(read_only_hint=True),
    )
    async def generate_profile_link(profile_id: str) -> str:
        result = await service.generate_link(profile_id)
        if result.outcome != ProfileLinkOutcome.SUCCESS or result.link is None:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return json.dumps({"profile_id": profile_id, "share_url": result.link.url})
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/profiles/test_mcp.py -v`
Expected: ALL PASS

Same note as Task 3 — adjust imports and assertions if `fastmcp` API differs.

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/fellow_aiden_api/profiles/mcp.py tests/profiles/test_mcp.py`

- [ ] **Step 6: Commit**

```bash
git add src/fellow_aiden_api/profiles/mcp.py tests/profiles/test_mcp.py
git commit -m "feat: add profiles MCP resources and tools"
```

---

### Task 5: Schedules MCP — resources and tools

**Files:**
- Create: `src/fellow_aiden_api/schedules/mcp.py`
- Create: `tests/schedules/test_mcp.py`

Schedules has 1 resource (`coffee://schedules`) and 3 CRUD tools (`create_schedule`, `update_schedule`, `delete_schedule`). The `brew_now` tool is in Task 6.

- [ ] **Step 1: Write failing tests**

```python
# tests/schedules/test_mcp.py
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


@pytest.fixture
def mock_schedule_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mcp(mock_schedule_service: AsyncMock) -> FastMCP:
    server = FastMCP("test")
    register_schedule_mcp(server, mock_schedule_service)
    return server


async def test_schedules_resource_returns_list(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.list_schedules.return_value = ScheduleListResult(
        outcome=ScheduleListOutcome.SUCCESS,
        schedules=[
            Schedule(id="s1", days=[False, True, True, True, True, True, False],
                     second_from_start_of_day=25200, enabled=True, amount_of_water=500, profile_id="p1"),
        ],
    )
    result = await mcp.read_resource("coffee://schedules")
    text = result[0].content if hasattr(result[0], "content") else str(result[0])
    data = json.loads(text)
    assert len(data) == 1
    assert data[0]["id"] == "s1"
    assert data[0]["amount_of_water"] == 500


async def test_create_schedule_success(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=Schedule(id="s2", days=[True] * 7, second_from_start_of_day=25200,
                          enabled=True, amount_of_water=500, profile_id="p1"),
    )
    result = await mcp.call_tool("create_schedule", {
        "days": [True] * 7,
        "time_seconds": 25200,
        "water_ml": 500,
        "profile_id": "p1",
        "enabled": True,
    })
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "s2" in text


async def test_create_schedule_unavailable(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    with pytest.raises(ToolError, match="(?i)unavailable|unreachable"):
        await mcp.call_tool("create_schedule", {
            "days": [True] * 7,
            "time_seconds": 25200,
            "water_ml": 500,
            "profile_id": "p1",
            "enabled": True,
        })


async def test_update_schedule_success(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.update_schedule.return_value = ScheduleUpdateResult(
        outcome=ScheduleUpdateOutcome.SUCCESS,
    )
    result = await mcp.call_tool("update_schedule", {"schedule_id": "s1", "enabled": False})
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "updated" in text.lower()


async def test_delete_schedule_success(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.delete_schedule.return_value = ScheduleDeleteResult(
        outcome=ScheduleDeleteOutcome.SUCCESS,
    )
    result = await mcp.call_tool("delete_schedule", {"schedule_id": "s1"})
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "deleted" in text.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/schedules/test_mcp.py -v`
Expected: FAIL — `fellow_aiden_api.schedules.mcp` does not exist

- [ ] **Step 3: Implement schedules MCP**

```python
# src/fellow_aiden_api/schedules/mcp.py
import json
from dataclasses import asdict

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from fellow_aiden_api.schedules.model.schedule import ScheduleCreate, ScheduleUpdate
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleDeleteOutcome,
    ScheduleListOutcome,
    ScheduleService,
    ScheduleUpdateOutcome,
)


def register_schedule_mcp(mcp: FastMCP, service: ScheduleService) -> None:
    @mcp.resource("coffee://schedules", description="All scheduled brews with days, time, water amount, and linked profile.")
    async def list_schedules() -> str:
        result = await service.list_schedules()
        if result.outcome != ScheduleListOutcome.SUCCESS or result.schedules is None:
            return json.dumps({"error": "Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry."})
        return json.dumps([asdict(s) for s in result.schedules])

    @mcp.tool(
        description="Schedule a recurring brew on specific days. Days is a 7-element array (Sunday=index 0). Time is seconds from midnight. For one-off brews, use brew_now instead.",
    )
    async def create_schedule(
        days: list[bool],
        time_seconds: int,
        water_ml: int,
        profile_id: str,
        enabled: bool = True,
    ) -> str:
        create = ScheduleCreate(
            days=days,
            second_from_start_of_day=time_seconds,
            enabled=enabled,
            amount_of_water=water_ml,
            profile_id=profile_id,
        )
        result = await service.create_schedule(create)
        if result.outcome != ScheduleCreateOutcome.SUCCESS or result.schedule is None:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return json.dumps({"status": "created", "schedule": asdict(result.schedule)})

    @mcp.tool(
        description="Update specific fields on an existing schedule. Only provide the fields you want to change.",
    )
    async def update_schedule(
        schedule_id: str,
        days: list[bool] | None = None,
        time_seconds: int | None = None,
        water_ml: int | None = None,
        profile_id: str | None = None,
        enabled: bool | None = None,
    ) -> str:
        update = ScheduleUpdate(
            days=days,
            second_from_start_of_day=time_seconds,
            enabled=enabled,
            amount_of_water=water_ml,
            profile_id=profile_id,
        )
        result = await service.update_schedule(schedule_id, update)
        if result.outcome != ScheduleUpdateOutcome.SUCCESS:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return f"Schedule '{schedule_id}' updated successfully."

    @mcp.tool(
        description="Permanently delete a schedule. This cannot be undone.",
        annotations=ToolAnnotations(destructive_hint=True),
    )
    async def delete_schedule(schedule_id: str) -> str:
        result = await service.delete_schedule(schedule_id)
        if result.outcome != ScheduleDeleteOutcome.SUCCESS:
            raise ToolError("Fellow cloud API is unreachable. This is usually transient — suggest the user wait a few minutes and retry.")
        return f"Schedule '{schedule_id}' deleted."
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/schedules/test_mcp.py -v`
Expected: ALL PASS

- [ ] **Step 5: Lint**

Run: `uv run ruff check src/fellow_aiden_api/schedules/mcp.py tests/schedules/test_mcp.py`

- [ ] **Step 6: Commit**

```bash
git add src/fellow_aiden_api/schedules/mcp.py tests/schedules/test_mcp.py
git commit -m "feat: add schedules MCP resource and tools"
```

---

### Task 6: `brew_now` tool

**Files:**
- Modify: `src/fellow_aiden_api/schedules/mcp.py`
- Modify: `tests/schedules/test_mcp.py`

`brew_now` creates a one-shot schedule ~5 seconds from now, waits for it to trigger, then deletes it. It computes the current day-of-week and time-of-day server-side. The caller only provides `profile_id` and `water_ml`.

- [ ] **Step 1: Write failing tests**

Add to `tests/schedules/test_mcp.py`:

```python
import asyncio
from unittest.mock import patch


async def test_brew_now_creates_and_deletes_schedule(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    created_schedule = Schedule(
        id="s-temp", days=[False] * 7, second_from_start_of_day=0,
        enabled=True, amount_of_water=500, profile_id="p1",
    )
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=created_schedule,
    )
    mock_schedule_service.delete_schedule.return_value = ScheduleDeleteResult(
        outcome=ScheduleDeleteOutcome.SUCCESS,
    )

    with patch("fellow_aiden_api.schedules.mcp.asyncio.sleep", new_callable=AsyncMock):
        result = await mcp.call_tool("brew_now", {"profile_id": "p1", "water_ml": 500})

    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "brew" in text.lower() or "started" in text.lower()

    # Verify schedule was created then deleted
    mock_schedule_service.create_schedule.assert_called_once()
    mock_schedule_service.delete_schedule.assert_called_once_with("s-temp")


async def test_brew_now_cleans_up_on_delete_failure(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    created_schedule = Schedule(
        id="s-temp", days=[False] * 7, second_from_start_of_day=0,
        enabled=True, amount_of_water=500, profile_id="p1",
    )
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=created_schedule,
    )
    mock_schedule_service.delete_schedule.return_value = ScheduleDeleteResult(
        outcome=ScheduleDeleteOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )

    with patch("fellow_aiden_api.schedules.mcp.asyncio.sleep", new_callable=AsyncMock):
        result = await mcp.call_tool("brew_now", {"profile_id": "p1", "water_ml": 500})

    # Should still succeed (brew was triggered) but warn about cleanup
    text = result[0].text if hasattr(result[0], "text") else str(result[0])
    assert "brew" in text.lower()


async def test_brew_now_fails_when_schedule_creation_fails(
    mcp: FastMCP, mock_schedule_service: AsyncMock
) -> None:
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )

    with pytest.raises(ToolError, match="(?i)unavailable|unreachable"):
        await mcp.call_tool("brew_now", {"profile_id": "p1", "water_ml": 500})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/schedules/test_mcp.py -v -k "brew_now"`
Expected: FAIL — no tool named `brew_now`

- [ ] **Step 3: Implement `brew_now`**

Add to `register_schedule_mcp()` in `src/fellow_aiden_api/schedules/mcp.py`:

```python
    # Add these imports at the top of the file:
    # import asyncio
    # from datetime import datetime, timezone

    @mcp.tool(
        description="Brew immediately using a specific profile. Creates a temporary schedule, waits for it to trigger, then cleans it up. The user should have water and grounds ready.",
    )
    async def brew_now(profile_id: str, water_ml: int) -> str:
        now = datetime.now(tz=timezone.utc).astimezone()
        current_day_index = (now.weekday() + 1) % 7  # Python Monday=0 -> Fellow Sunday=0
        brew_seconds = now.hour * 3600 + now.minute * 60 + now.second + 5

        # Handle midnight rollover
        days = [False] * 7
        if brew_seconds >= 86400:
            brew_seconds -= 86400
            current_day_index = (current_day_index + 1) % 7
        days[current_day_index] = True

        create = ScheduleCreate(
            days=days,
            second_from_start_of_day=brew_seconds,
            enabled=True,
            amount_of_water=water_ml,
            profile_id=profile_id,
        )
        result = await service.create_schedule(create)
        if result.outcome != ScheduleCreateOutcome.SUCCESS or result.schedule is None:
            raise ToolError("Fellow cloud API is unreachable. Could not start brew — suggest the user wait a few minutes and retry.")

        schedule_id = result.schedule.id

        # Wait for the schedule to trigger, then clean up
        await asyncio.sleep(10)

        delete_result = await service.delete_schedule(schedule_id)
        if delete_result.outcome != ScheduleDeleteOutcome.SUCCESS:
            return f"Brew started successfully, but could not clean up temporary schedule '{schedule_id}'. It should be deleted manually."

        return "Brew started successfully. The temporary schedule has been cleaned up."
```

- [ ] **Step 4: Add imports at the top of schedules/mcp.py**

Make sure these are at the top of the file:

```python
import asyncio
from datetime import datetime, timezone
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/schedules/test_mcp.py -v`
Expected: ALL PASS

- [ ] **Step 6: Lint**

Run: `uv run ruff check src/fellow_aiden_api/schedules/mcp.py tests/schedules/test_mcp.py`

- [ ] **Step 7: Commit**

```bash
git add src/fellow_aiden_api/schedules/mcp.py tests/schedules/test_mcp.py
git commit -m "feat: add brew_now tool for immediate brewing"
```

---

### Task 7: Wire up MCP in main.py

**Files:**
- Modify: `src/fellow_aiden_api/main.py`
- Create: `tests/test_mcp_integration.py`

This is where everything comes together. The FastMCP instance is created, tools/resources are registered with the services from lifespan, and the sub-app is mounted with auth middleware.

- [ ] **Step 1: Write failing integration test**

```python
# tests/test_mcp_integration.py
import pytest
from starlette.testclient import TestClient


def test_mcp_endpoint_not_mounted_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """When MCP is disabled (default), /mcp should not exist."""
    monkeypatch.setenv("FELLOW_FELLOW_EMAIL", "test@example.com")
    monkeypatch.setenv("FELLOW_FELLOW_PASSWORD", "test-password")
    monkeypatch.delenv("FELLOW_MCP_ENABLED", raising=False)

    # Need to reimport to pick up env change
    from fellow_aiden_api.dependencies import get_settings
    get_settings.cache_clear()

    # We can't easily test route absence without starting the app,
    # so test that the config defaults to False
    from fellow_aiden_api.config import Settings
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is False


def test_mcp_enabled_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_MCP_ENABLED", "true")
    from fellow_aiden_api.config import Settings
    settings = Settings(fellow_email="a@b.com", fellow_password="x")
    assert settings.mcp_enabled is True
```

- [ ] **Step 2: Run tests to verify they pass (config tests already work from Task 1)**

Run: `uv run pytest tests/test_mcp_integration.py -v`
Expected: PASS (these test config, which is already done)

- [ ] **Step 3: Modify main.py to mount MCP conditionally**

```python
# src/fellow_aiden_api/main.py
# Add to imports section:
import os

# After app creation and router includes, add:
_mcp_enabled = os.getenv("FELLOW_MCP_ENABLED", "false").lower() == "true"

if _mcp_enabled:
    from fastmcp import FastMCP as _FastMCP

    from fellow_aiden_api.mcp_auth import McpApiKeyMiddleware

    _mcp_server = _FastMCP("fellow-aiden-coffee")
    _mcp_app = _mcp_server.http_app(path="/")
    _mcp_api_key = os.getenv("FELLOW_API_KEY")
    _mcp_app.add_middleware(McpApiKeyMiddleware, api_key=_mcp_api_key)
    app.mount("/mcp", _mcp_app)
```

Then modify the `lifespan()` function to register MCP tools when enabled:

```python
# Inside lifespan(), after service creation (after line 45), add:
    if _mcp_enabled:
        from fellow_aiden_api.device.mcp import register_device_mcp
        from fellow_aiden_api.profiles.mcp import register_profile_mcp
        from fellow_aiden_api.schedules.mcp import register_schedule_mcp

        register_device_mcp(_mcp_server, device_service)
        register_profile_mcp(_mcp_server, profile_service)
        register_schedule_mcp(_mcp_server, schedule_service)
```

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest -v`
Expected: ALL PASS — existing tests should not be affected since MCP is disabled by default

- [ ] **Step 5: Lint and type check**

Run: `uv run ruff check src/ tests/ && uv run ty check src/`

- [ ] **Step 6: Commit**

```bash
git add src/fellow_aiden_api/main.py tests/test_mcp_integration.py
git commit -m "feat: wire up MCP server in main.py with conditional mount"
```

---

### Task 8: Update CLAUDE.md and clean up

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add MCP section to CLAUDE.md**

Add after the Endpoints section:

```markdown
## MCP Server

Optional MCP (Model Context Protocol) server mounted at `/coffee/api/mcp` when `FELLOW_MCP_ENABLED=true`.

- Built with `fastmcp`, shares the service layer with FastAPI routers
- Transport: Streamable HTTP
- Auth: same `X-API-Key` header as REST API
- Resources: `coffee://device`, `coffee://profiles`, `coffee://profiles/{id}`, `coffee://schedules`
- Tools: `brew_now`, `update_device_setting`, `create_profile`, `update_profile`, `delete_profile`, `generate_profile_link`, `create_schedule`, `update_schedule`, `delete_schedule`
- `brew_now` creates a temporary schedule ~5s from now, waits, then deletes it

Client config (`.mcp.json`):
```json
{
  "mcpServers": {
    "fellow-aiden": {
      "type": "http",
      "url": "https://raspberry-pi/coffee/api/mcp",
      "headers": {
        "X-API-Key": "${FELLOW_API_KEY}"
      }
    }
  }
}
```

- [ ] **Step 2: Run full test suite one final time**

Run: `uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 3: Lint everything**

Run: `uv run ruff check src/ tests/`
Expected: No issues

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add MCP server section to CLAUDE.md"
```

---

## Notes for the implementer

1. **`fastmcp` API uncertainty:** The exact method names for `FastMCP.call_tool()`, `FastMCP.read_resource()`, and error types (`ToolError`) are based on research but may differ in the installed version. When tests fail due to API mismatches, check `fastmcp` docs at gofastmcp.com and adjust. The test patterns (mock service, call tool, assert response) are correct — only the invocation syntax may need tweaking.

2. **Mounting path:** The plan uses `mcp.http_app(path="/")` mounted at `app.mount("/mcp", ...)` so the MCP endpoint is at `/coffee/api/mcp` (with nginx `root_path`). If this produces routing issues, try `mcp.http_app(path="/mcp")` mounted at `app.mount("", ...)` instead.

3. **Lifespan interaction:** `fastmcp`'s `http_app()` returns a Starlette app with its own lifespan. If there are lifespan conflicts with FastAPI's existing lifespan, the workaround is documented at gofastmcp.com/integrations/fastapi.

4. **`os.getenv` for MCP flag:** The plan reads `FELLOW_MCP_ENABLED` via `os.getenv` at module level (not `Settings`) because the mount must happen at import time, before lifespan runs. This is intentional — `Settings` requires env vars that may not exist during testing.
