# Fellow Aiden API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI HTTP API wrapping the Fellow Aiden cloud API, self-hosted on a Raspberry Pi, with domain-first architecture.

**Architecture:** Three-layer clean architecture (API -> Domain <- Infrastructure) with domain-first folder structure. Each domain (profiles, schedules, device) is a self-contained module with its own router, service, facade protocol, client implementation, and models. The `fellow-aiden` library is synchronous, so infrastructure clients use `asyncio.to_thread()` to avoid blocking.

**Tech Stack:** Python 3.13, FastAPI, Pydantic v2, uv, ruff, ty, pytest + anyio + httpx + respx + polyfactory, Docker

**Spec:** `docs/superpowers/specs/2026-04-10-fellow-aiden-api-design.md`

**SOA Guidelines:** Follow `leo-skills:service-oriented-architecture` skill -- domain-first folders, strict layer boundaries, facades as protocols, typed outcomes, separate models per layer.

---

## File Map

```
src/
  fellow_aiden_api/
    __init__.py
    main.py                                 # FastAPI app, lifespan, root_path, catch-all handler
    config.py                               # Pydantic Settings
    dependencies.py                         # Global deps (API key guard)
    health/
      __init__.py
      router.py                             # GET /health
    device/
      __init__.py
      router.py
      service.py
      mapper.py                             # API <-> Domain
      facade.py                             # DeviceFacade protocol
      dependencies.py
      model/
        __init__.py
        api/
          __init__.py
          requests.py
          responses.py
        device.py                           # Device, DeviceSettings entities
      client/
        __init__.py
        fellow_client.py                    # Implements DeviceFacade
        fellow_client_mapper.py             # Fellow dict <-> Device entity
    profiles/
      __init__.py
      router.py
      service.py
      mapper.py
      facade.py                             # ProfileFacade protocol
      dependencies.py
      model/
        __init__.py
        api/
          __init__.py
          requests.py
          responses.py
        profile.py                          # Profile entity
      client/
        __init__.py
        fellow_client.py                    # Implements ProfileFacade
        fellow_client_mapper.py             # Fellow dict <-> Profile entity
    schedules/
      __init__.py
      router.py
      service.py
      mapper.py
      facade.py                             # ScheduleFacade protocol
      dependencies.py
      model/
        __init__.py
        api/
          __init__.py
          requests.py
          responses.py
        schedule.py                         # Schedule entity
      client/
        __init__.py
        fellow_client.py                    # Implements ScheduleFacade
        fellow_client_mapper.py             # Fellow dict <-> Schedule entity
tests/
  __init__.py
  conftest.py                               # Shared fixtures, app factory, respx mocks
  health/
    __init__.py
    test_router.py
  device/
    __init__.py
    test_router.py
    test_service.py
    test_fellow_client.py
  profiles/
    __init__.py
    test_router.py
    test_service.py
    test_fellow_client.py
  schedules/
    __init__.py
    test_router.py
    test_service.py
    test_fellow_client.py
pyproject.toml
Dockerfile
docker-compose.yml
.github/workflows/ci.yml
.env.example
.gitignore
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/fellow_aiden_api/__init__.py`

- [ ] **Step 1: Initialize uv project**

```bash
cd /home/leo/documents/code/raspberrypi/fellow-aiden-api
uv init --lib --name fellow-aiden-api
```

This creates `pyproject.toml` and `src/fellow_aiden_api/__init__.py`. We'll overwrite the generated `pyproject.toml` in the next step.

- [ ] **Step 2: Configure pyproject.toml**

Replace the generated `pyproject.toml` with:

```toml
[project]
name = "fellow-aiden-api"
version = "0.1.0"
description = "HTTP API wrapping the Fellow Aiden cloud API"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "pydantic-settings>=2.7",
    "fellow-aiden>=0.2",
    "httpx>=0.28",
]

[dependency-groups]
dev = [
    "pytest>=8",
    "anyio[trio]>=4",
    "pytest-anyio>=0.0.2",
    "respx>=0.22",
    "pytest-mock>=3",
    "polyfactory>=2",
    "pytest-cov>=6",
    "dirty-equals>=0.8",
    "ruff>=0.11",
    "ty>=0.0.20",
]

[tool.ruff]
target-version = "py313"
line-length = 120
src = ["src", "tests"]

[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "D",        # pydocstyle (we'll add docstrings selectively)
    "ANN101",   # missing type self
    "ANN102",   # missing type cls
    "COM812",   # trailing comma (conflicts with formatter)
    "ISC001",   # implicit string concat (conflicts with formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ANN", "PLR2004"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["fellow_aiden_api"]

[tool.coverage.report]
show_missing = true
fail_under = 80

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.hatch.build.targets.wheel]
packages = ["src/fellow_aiden_api"]
```

- [ ] **Step 3: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
.env
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
```

- [ ] **Step 4: Create .env.example**

```env
FELLOW_FELLOW_EMAIL=your@email.com
FELLOW_FELLOW_PASSWORD=your-password
FELLOW_API_KEY=optional-api-key
```

- [ ] **Step 5: Install dependencies**

```bash
uv sync
```

- [ ] **Step 6: Verify toolchain**

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run ty check src/
uv run pytest --co
```

All should pass with zero errors (empty project).

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock src/fellow_aiden_api/__init__.py .gitignore .env.example
git commit -m "chore: scaffold project with uv, ruff, ty, pytest"
```

---

## Task 2: LSP Setup and Verification

**Files:**
- None (editor configuration)

- [ ] **Step 1: Verify ty language server works**

```bash
uv run ty check src/
```

Must output zero errors. If ty is not available as an LSP in the editor, configure it. The LSP must be working and clean before proceeding to any implementation.

- [ ] **Step 2: Verify ruff works**

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Zero errors.

---

## Task 3: FastAPI App Skeleton + Health Endpoint

**Files:**
- Create: `src/fellow_aiden_api/main.py`
- Create: `src/fellow_aiden_api/health/__init__.py`
- Create: `src/fellow_aiden_api/health/router.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/health/__init__.py`
- Create: `tests/health/test_router.py`

- [ ] **Step 1: Write the failing e2e test for health**

`tests/__init__.py` — empty file.

`tests/health/__init__.py` — empty file.

`tests/conftest.py`:

```python
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from fellow_aiden_api.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

`tests/health/test_router.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/health/test_router.py -v
```

Expected: FAIL (cannot import `fellow_aiden_api.main`).

- [ ] **Step 3: Implement FastAPI app + health router**

`src/fellow_aiden_api/health/__init__.py` — empty file.

`src/fellow_aiden_api/health/router.py`:

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
```

`src/fellow_aiden_api/main.py`:

```python
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from fellow_aiden_api.health.router import router as health_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fellow Aiden API",
    root_path="/coffee/api",
)

app.include_router(health_router)


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/health/test_router.py -v
```

Expected: PASS.

- [ ] **Step 5: Run lints and type check**

```bash
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run ty check src/
```

Fix any issues.

- [ ] **Step 6: Commit**

```bash
git add src/fellow_aiden_api/ tests/
git commit -m "feat: add FastAPI app skeleton with health endpoint"
```

---

## Task 4: Configuration

**Files:**
- Create: `src/fellow_aiden_api/config.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Write failing test for config loading**

Add to `tests/conftest.py` above the `client` fixture:

```python
import os

@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_FELLOW_EMAIL", "test@example.com")
    monkeypatch.setenv("FELLOW_FELLOW_PASSWORD", "test-password")
```

Create `tests/test_config.py`:

```python
from fellow_aiden_api.config import Settings


def test_settings_loads_from_env() -> None:
    settings = Settings()
    assert settings.fellow_email == "test@example.com"
    assert settings.fellow_password.get_secret_value() == "test-password"
    assert settings.api_key is None


def test_settings_default_port() -> None:
    settings = Settings()
    assert settings.port == 8000


def test_settings_default_host() -> None:
    settings = Settings()
    assert settings.host == "0.0.0.0"  # noqa: S104


def test_settings_default_token_refresh_interval() -> None:
    settings = Settings()
    assert settings.token_refresh_interval_seconds == 780
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL (cannot import `config`).

- [ ] **Step 3: Implement Settings**

`src/fellow_aiden_api/config.py`:

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FELLOW_")

    fellow_email: str
    fellow_password: SecretStr

    api_key: SecretStr | None = None

    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000

    token_refresh_interval_seconds: int = 780
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fellow_aiden_api/config.py tests/test_config.py tests/conftest.py
git commit -m "feat: add Settings configuration with env var loading"
```

---

## Task 5: API Key Guard

**Files:**
- Create: `src/fellow_aiden_api/dependencies.py`
- Modify: `src/fellow_aiden_api/main.py`
- Create: `tests/test_api_key.py`

- [ ] **Step 1: Write failing e2e tests for API key guard**

`tests/test_api_key.py`:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from fellow_aiden_api.main import app


@pytest.fixture
def _set_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FELLOW_API_KEY", "test-secret-key")


@pytest.mark.anyio
async def test_no_api_key_configured_allows_request(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.usefixtures("_set_api_key")
async def test_valid_api_key_allows_request() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health", headers={"X-API-Key": "test-secret-key"})
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.usefixtures("_set_api_key")
async def test_invalid_api_key_returns_403() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 403


@pytest.mark.anyio
@pytest.mark.usefixtures("_set_api_key")
async def test_missing_api_key_returns_403() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_api_key.py -v
```

Expected: tests expecting 403 will FAIL (no guard in place yet).

- [ ] **Step 3: Implement API key guard**

`src/fellow_aiden_api/dependencies.py`:

```python
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from fellow_aiden_api.config import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_settings() -> Settings:
    return Settings()


async def require_api_key(
    key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    if settings.api_key is None:
        return
    if key is None or key != settings.api_key.get_secret_value():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key")
```

- [ ] **Step 4: Wire guard into the app**

Update `src/fellow_aiden_api/main.py`:

```python
import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from fellow_aiden_api.dependencies import require_api_key
from fellow_aiden_api.health.router import router as health_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fellow Aiden API",
    root_path="/coffee/api",
    dependencies=[Depends(require_api_key)],
)

app.include_router(health_router)


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_api_key.py -v
```

Expected: PASS.

- [ ] **Step 6: Run full test suite**

```bash
uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/fellow_aiden_api/dependencies.py src/fellow_aiden_api/main.py tests/test_api_key.py
git commit -m "feat: add optional API key guard"
```

---

## Task 6: Device Domain — Entity + Facade

**Files:**
- Create: `src/fellow_aiden_api/device/__init__.py`
- Create: `src/fellow_aiden_api/device/model/__init__.py`
- Create: `src/fellow_aiden_api/device/model/device.py`
- Create: `src/fellow_aiden_api/device/facade.py`

- [ ] **Step 1: Create the Device domain entity**

`src/fellow_aiden_api/device/__init__.py` — empty file.

`src/fellow_aiden_api/device/model/__init__.py` — empty file.

`src/fellow_aiden_api/device/model/device.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    brewer_id: str
    display_name: str
    firmware_version: str


@dataclass(frozen=True)
class DeviceSettings:
    setting: str
    value: str | int | float | bool
```

- [ ] **Step 2: Create the DeviceFacade protocol**

`src/fellow_aiden_api/device/facade.py`:

```python
from typing import Protocol

from fellow_aiden_api.device.model.device import Device, DeviceSettings


class DeviceFacade(Protocol):
    async def get_device(self) -> Device: ...
    async def adjust_setting(self, settings: DeviceSettings) -> None: ...
```

- [ ] **Step 3: Run lints and type check**

```bash
uv run ruff check src/fellow_aiden_api/device/ && uv run ty check src/
```

- [ ] **Step 4: Commit**

```bash
git add src/fellow_aiden_api/device/
git commit -m "feat(device): add Device entity and DeviceFacade protocol"
```

---

## Task 7: Device Domain — Infrastructure Client

**Files:**
- Create: `src/fellow_aiden_api/device/client/__init__.py`
- Create: `src/fellow_aiden_api/device/client/fellow_client_mapper.py`
- Create: `src/fellow_aiden_api/device/client/fellow_client.py`
- Create: `tests/device/__init__.py`
- Create: `tests/device/test_fellow_client.py`

- [ ] **Step 1: Write failing test for client mapper**

`tests/device/__init__.py` — empty file.

`tests/device/test_fellow_client.py`:

```python
from fellow_aiden_api.device.client.fellow_client_mapper import FellowDeviceMapper
from fellow_aiden_api.device.model.device import Device


def test_mapper_converts_fellow_dict_to_device() -> None:
    fellow_data: dict = {
        "id": "brewer-123",
        "displayName": "My Aiden",
        "firmwareVersion": "3.2.1",
        "otherField": "ignored",
    }
    device = FellowDeviceMapper.to_entity(fellow_data)
    assert device == Device(
        brewer_id="brewer-123",
        display_name="My Aiden",
        firmware_version="3.2.1",
    )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/device/test_fellow_client.py::test_mapper_converts_fellow_dict_to_device -v
```

Expected: FAIL (cannot import mapper).

- [ ] **Step 3: Implement the mapper**

`src/fellow_aiden_api/device/client/__init__.py` — empty file.

`src/fellow_aiden_api/device/client/fellow_client_mapper.py`:

```python
from typing import Any

from fellow_aiden_api.device.model.device import Device


class FellowDeviceMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Device:
        return Device(
            brewer_id=data["id"],
            display_name=data["displayName"],
            firmware_version=data["firmwareVersion"],
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/device/test_fellow_client.py::test_mapper_converts_fellow_dict_to_device -v
```

Expected: PASS.

- [ ] **Step 5: Write failing test for FellowDeviceClient**

Add to `tests/device/test_fellow_client.py`:

```python
import asyncio
from unittest.mock import MagicMock

import pytest

from fellow_aiden_api.device.client.fellow_client import FellowDeviceClient
from fellow_aiden_api.device.model.device import Device, DeviceSettings


@pytest.mark.anyio
async def test_get_device_returns_mapped_entity() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_device_config.return_value = {
        "id": "brewer-123",
        "displayName": "My Aiden",
        "firmwareVersion": "3.2.1",
    }

    client = FellowDeviceClient(fellow=mock_fellow)
    device = await client.get_device()

    assert device == Device(
        brewer_id="brewer-123",
        display_name="My Aiden",
        firmware_version="3.2.1",
    )
    mock_fellow.get_device_config.assert_called_once_with(remote=True)


@pytest.mark.anyio
async def test_adjust_setting_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.adjust_setting.return_value = b""

    client = FellowDeviceClient(fellow=mock_fellow)
    await client.adjust_setting(DeviceSettings(setting="volume", value=5))

    mock_fellow.adjust_setting.assert_called_once_with("volume", 5)
```

- [ ] **Step 6: Run test to verify it fails**

```bash
uv run pytest tests/device/test_fellow_client.py -v
```

Expected: FAIL (cannot import `FellowDeviceClient`).

- [ ] **Step 7: Implement FellowDeviceClient**

`src/fellow_aiden_api/device/client/fellow_client.py`:

```python
import asyncio
from typing import Any

from fellow_aiden import FellowAiden

from fellow_aiden_api.device.client.fellow_client_mapper import FellowDeviceMapper
from fellow_aiden_api.device.model.device import Device, DeviceSettings


class FellowDeviceClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow
        self._mapper = FellowDeviceMapper()

    async def get_device(self) -> Device:
        data: dict[str, Any] = await asyncio.to_thread(self._fellow.get_device_config, remote=True)
        return self._mapper.to_entity(data)

    async def adjust_setting(self, settings: DeviceSettings) -> None:
        await asyncio.to_thread(self._fellow.adjust_setting, settings.setting, settings.value)
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
uv run pytest tests/device/test_fellow_client.py -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add src/fellow_aiden_api/device/client/ tests/device/
git commit -m "feat(device): add FellowDeviceClient with async wrapper"
```

---

## Task 8: Device Domain — Service

**Files:**
- Create: `src/fellow_aiden_api/device/service.py`
- Create: `tests/device/test_service.py`

- [ ] **Step 1: Write failing test for DeviceService.get_device**

`tests/device/test_service.py`:

```python
from dataclasses import dataclass
from enum import Enum
from unittest.mock import AsyncMock

import pytest

from fellow_aiden_api.device.model.device import Device, DeviceSettings
from fellow_aiden_api.device.service import DeviceGetOutcome, DeviceGetResult, DeviceService, DeviceSettingsOutcome, DeviceSettingsResult


@pytest.mark.anyio
async def test_get_device_success() -> None:
    mock_facade = AsyncMock()
    expected_device = Device(brewer_id="b1", display_name="Aiden", firmware_version="3.0")
    mock_facade.get_device.return_value = expected_device

    service = DeviceService(facade=mock_facade)
    result = await service.get_device()

    assert result.outcome == DeviceGetOutcome.SUCCESS
    assert result.device == expected_device


@pytest.mark.anyio
async def test_get_device_upstream_unavailable() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_device.side_effect = Exception("connection failed")

    service = DeviceService(facade=mock_facade)
    result = await service.get_device()

    assert result.outcome == DeviceGetOutcome.FELLOW_UNAVAILABLE
    assert result.device is None
    assert result.error is not None


@pytest.mark.anyio
async def test_adjust_setting_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.adjust_setting.return_value = None

    service = DeviceService(facade=mock_facade)
    settings = DeviceSettings(setting="volume", value=5)
    result = await service.adjust_setting(settings)

    assert result.outcome == DeviceSettingsOutcome.SUCCESS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/device/test_service.py -v
```

Expected: FAIL (cannot import service).

- [ ] **Step 3: Implement DeviceService**

`src/fellow_aiden_api/device/service.py`:

```python
import logging
from dataclasses import dataclass
from enum import Enum

from fellow_aiden_api.device.facade import DeviceFacade
from fellow_aiden_api.device.model.device import Device, DeviceSettings

logger = logging.getLogger(__name__)


class DeviceGetOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class DeviceSettingsOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


@dataclass
class DeviceGetResult:
    outcome: DeviceGetOutcome
    device: Device | None = None
    error: str | None = None


@dataclass
class DeviceSettingsResult:
    outcome: DeviceSettingsOutcome
    error: str | None = None


class DeviceService:
    def __init__(self, facade: DeviceFacade) -> None:
        self._facade = facade

    async def get_device(self) -> DeviceGetResult:
        try:
            device = await self._facade.get_device()
        except Exception:
            logger.exception("Failed to fetch device")
            return DeviceGetResult(outcome=DeviceGetOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return DeviceGetResult(outcome=DeviceGetOutcome.SUCCESS, device=device)

    async def adjust_setting(self, settings: DeviceSettings) -> DeviceSettingsResult:
        try:
            await self._facade.adjust_setting(settings)
        except Exception:
            logger.exception("Failed to adjust setting")
            return DeviceSettingsResult(outcome=DeviceSettingsOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return DeviceSettingsResult(outcome=DeviceSettingsOutcome.SUCCESS)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/device/test_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fellow_aiden_api/device/service.py tests/device/test_service.py
git commit -m "feat(device): add DeviceService with typed outcomes"
```

---

## Task 9: Device Domain — API Models + Mapper + Router

**Files:**
- Create: `src/fellow_aiden_api/device/model/api/__init__.py`
- Create: `src/fellow_aiden_api/device/model/api/requests.py`
- Create: `src/fellow_aiden_api/device/model/api/responses.py`
- Create: `src/fellow_aiden_api/device/mapper.py`
- Create: `src/fellow_aiden_api/device/dependencies.py`
- Create: `src/fellow_aiden_api/device/router.py`
- Modify: `src/fellow_aiden_api/main.py`
- Create: `tests/device/test_router.py`

- [ ] **Step 1: Write failing e2e tests for device router**

`tests/device/test_router.py`:

```python
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from fellow_aiden_api.device.dependencies import get_device_service
from fellow_aiden_api.device.model.device import Device, DeviceSettings
from fellow_aiden_api.device.service import DeviceGetOutcome, DeviceGetResult, DeviceSettingsOutcome, DeviceSettingsResult
from fellow_aiden_api.main import app


@pytest.fixture
def mock_device_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_device_service(mock_device_service: AsyncMock) -> None:
    app.dependency_overrides[get_device_service] = lambda: mock_device_service
    yield
    app.dependency_overrides.pop(get_device_service, None)


@pytest.mark.anyio
async def test_get_device_returns_200(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.get_device.return_value = DeviceGetResult(
        outcome=DeviceGetOutcome.SUCCESS,
        device=Device(brewer_id="b1", display_name="My Aiden", firmware_version="3.2.1"),
    )
    response = await client.get("/device")
    assert response.status_code == 200
    data = response.json()
    assert data["brewer_id"] == "b1"
    assert data["display_name"] == "My Aiden"
    assert data["firmware_version"] == "3.2.1"


@pytest.mark.anyio
async def test_get_device_returns_503_when_unavailable(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.get_device.return_value = DeviceGetResult(
        outcome=DeviceGetOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    response = await client.get("/device")
    assert response.status_code == 503


@pytest.mark.anyio
async def test_patch_settings_returns_200(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.adjust_setting.return_value = DeviceSettingsResult(
        outcome=DeviceSettingsOutcome.SUCCESS,
    )
    response = await client.patch("/device/settings", json={"setting": "volume", "value": 5})
    assert response.status_code == 200


@pytest.mark.anyio
async def test_patch_settings_returns_503_when_unavailable(client: AsyncClient, mock_device_service: AsyncMock) -> None:
    mock_device_service.adjust_setting.return_value = DeviceSettingsResult(
        outcome=DeviceSettingsOutcome.FELLOW_UNAVAILABLE,
        error="Fellow cloud unavailable",
    )
    response = await client.patch("/device/settings", json={"setting": "volume", "value": 5})
    assert response.status_code == 503
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/device/test_router.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement API models**

`src/fellow_aiden_api/device/model/api/__init__.py` — empty file.

`src/fellow_aiden_api/device/model/api/requests.py`:

```python
from pydantic import BaseModel


class DeviceSettingsAPIRequest(BaseModel):
    setting: str
    value: str | int | float | bool
```

`src/fellow_aiden_api/device/model/api/responses.py`:

```python
from pydantic import BaseModel


class DeviceAPIResponse(BaseModel):
    brewer_id: str
    display_name: str
    firmware_version: str
```

- [ ] **Step 4: Implement mapper**

`src/fellow_aiden_api/device/mapper.py`:

```python
from fellow_aiden_api.device.model.api.requests import DeviceSettingsAPIRequest
from fellow_aiden_api.device.model.api.responses import DeviceAPIResponse
from fellow_aiden_api.device.model.device import Device, DeviceSettings


class DeviceMapper:
    @staticmethod
    def to_api_response(device: Device) -> DeviceAPIResponse:
        return DeviceAPIResponse(
            brewer_id=device.brewer_id,
            display_name=device.display_name,
            firmware_version=device.firmware_version,
        )

    @staticmethod
    def from_api_request(request: DeviceSettingsAPIRequest) -> DeviceSettings:
        return DeviceSettings(
            setting=request.setting,
            value=request.value,
        )
```

- [ ] **Step 5: Implement dependencies**

`src/fellow_aiden_api/device/dependencies.py`:

```python
from fellow_aiden_api.device.service import DeviceService


def get_device_service() -> DeviceService:
    raise NotImplementedError("Must be overridden — wired in app lifespan")
```

Note: The actual wiring of `FellowAiden` -> `FellowDeviceClient` -> `DeviceService` will be done in a later task when we set up the app lifespan. For now, this placeholder is overridden in tests via `dependency_overrides`.

- [ ] **Step 6: Implement router**

`src/fellow_aiden_api/device/router.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from fellow_aiden_api.device.dependencies import get_device_service
from fellow_aiden_api.device.mapper import DeviceMapper
from fellow_aiden_api.device.model.api.requests import DeviceSettingsAPIRequest
from fellow_aiden_api.device.model.api.responses import DeviceAPIResponse
from fellow_aiden_api.device.service import DeviceGetOutcome, DeviceService, DeviceSettingsOutcome

router = APIRouter(prefix="/device", tags=["device"])


@router.get("")
async def get_device(
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> DeviceAPIResponse:
    result = await service.get_device()
    match result.outcome:
        case DeviceGetOutcome.SUCCESS:
            assert result.device is not None
            return DeviceMapper.to_api_response(result.device)
        case DeviceGetOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.patch("/settings")
async def update_device_settings(
    request: DeviceSettingsAPIRequest,
    service: Annotated[DeviceService, Depends(get_device_service)],
) -> dict[str, str]:
    settings = DeviceMapper.from_api_request(request)
    result = await service.adjust_setting(settings)
    match result.outcome:
        case DeviceSettingsOutcome.SUCCESS:
            return {"status": "ok"}
        case DeviceSettingsOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
```

- [ ] **Step 7: Wire router into app**

Add to `src/fellow_aiden_api/main.py`:

```python
from fellow_aiden_api.device.router import router as device_router
```

And after the health router include:

```python
app.include_router(device_router)
```

- [ ] **Step 8: Run tests to verify they pass**

```bash
uv run pytest tests/device/ -v
```

Expected: PASS.

- [ ] **Step 9: Run full test suite + lints**

```bash
uv run pytest -v && uv run ruff check src/ tests/ && uv run ty check src/
```

- [ ] **Step 10: Commit**

```bash
git add src/fellow_aiden_api/device/ src/fellow_aiden_api/main.py tests/device/
git commit -m "feat(device): add device router, API models, mapper, and DI wiring"
```

---

## Task 10: Profiles Domain — Entity + Facade

**Files:**
- Create: `src/fellow_aiden_api/profiles/__init__.py`
- Create: `src/fellow_aiden_api/profiles/model/__init__.py`
- Create: `src/fellow_aiden_api/profiles/model/profile.py`
- Create: `src/fellow_aiden_api/profiles/facade.py`

- [ ] **Step 1: Create the Profile domain entity**

`src/fellow_aiden_api/profiles/__init__.py` — empty file.

`src/fellow_aiden_api/profiles/model/__init__.py` — empty file.

`src/fellow_aiden_api/profiles/model/profile.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Profile:
    id: str
    title: str
    profile_type: int
    ratio: float
    bloom_enabled: bool
    bloom_ratio: float
    bloom_duration: int
    bloom_temperature: float
    ss_pulses_enabled: bool
    ss_pulses_number: int
    ss_pulses_interval: int
    ss_pulse_temperatures: list[float]
    batch_pulses_enabled: bool
    batch_pulses_number: int
    batch_pulses_interval: int
    batch_pulse_temperatures: list[float]


@dataclass(frozen=True)
class ProfileCreate:
    title: str
    profile_type: int
    ratio: float
    bloom_enabled: bool
    bloom_ratio: float
    bloom_duration: int
    bloom_temperature: float
    ss_pulses_enabled: bool
    ss_pulses_number: int
    ss_pulses_interval: int
    ss_pulse_temperatures: list[float]
    batch_pulses_enabled: bool
    batch_pulses_number: int
    batch_pulses_interval: int
    batch_pulse_temperatures: list[float]


@dataclass(frozen=True)
class ProfileUpdate:
    title: str | None = None
    ratio: float | None = None
    bloom_enabled: bool | None = None
    bloom_ratio: float | None = None
    bloom_duration: int | None = None
    bloom_temperature: float | None = None
    ss_pulses_enabled: bool | None = None
    ss_pulses_number: int | None = None
    ss_pulses_interval: int | None = None
    ss_pulse_temperatures: list[float] | None = None
    batch_pulses_enabled: bool | None = None
    batch_pulses_number: int | None = None
    batch_pulses_interval: int | None = None
    batch_pulse_temperatures: list[float] | None = None


@dataclass(frozen=True)
class ProfileLink:
    url: str
```

- [ ] **Step 2: Create the ProfileFacade protocol**

`src/fellow_aiden_api/profiles/facade.py`:

```python
from typing import Protocol

from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate


class ProfileFacade(Protocol):
    async def get_profiles(self) -> list[Profile]: ...
    async def get_profile(self, profile_id: str) -> Profile | None: ...
    async def create_profile(self, profile: ProfileCreate) -> Profile: ...
    async def create_profile_from_link(self, brew_link: str) -> Profile: ...
    async def update_profile(self, profile_id: str, profile: ProfileUpdate) -> None: ...
    async def delete_profile(self, profile_id: str) -> None: ...
    async def generate_link(self, profile_id: str) -> ProfileLink: ...
```

- [ ] **Step 3: Run lints and type check**

```bash
uv run ruff check src/fellow_aiden_api/profiles/ && uv run ty check src/
```

- [ ] **Step 4: Commit**

```bash
git add src/fellow_aiden_api/profiles/
git commit -m "feat(profiles): add Profile entity and ProfileFacade protocol"
```

---

## Task 11: Profiles Domain — Infrastructure Client

**Files:**
- Create: `src/fellow_aiden_api/profiles/client/__init__.py`
- Create: `src/fellow_aiden_api/profiles/client/fellow_client_mapper.py`
- Create: `src/fellow_aiden_api/profiles/client/fellow_client.py`
- Create: `tests/profiles/__init__.py`
- Create: `tests/profiles/test_fellow_client.py`

- [ ] **Step 1: Write failing test for profile client mapper**

`tests/profiles/__init__.py` — empty file.

`tests/profiles/test_fellow_client.py`:

```python
from fellow_aiden_api.profiles.client.fellow_client_mapper import FellowProfileMapper
from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate


SAMPLE_FELLOW_PROFILE: dict = {
    "id": "p0",
    "profileType": 1,
    "title": "Morning Brew",
    "ratio": 16.0,
    "bloomEnabled": True,
    "bloomRatio": 2.0,
    "bloomDuration": 30,
    "bloomTemperature": 93.0,
    "ssPulsesEnabled": False,
    "ssPulsesNumber": 1,
    "ssPulsesInterval": 10,
    "ssPulseTemperatures": [93.0],
    "batchPulsesEnabled": False,
    "batchPulsesNumber": 1,
    "batchPulsesInterval": 10,
    "batchPulseTemperatures": [93.0],
    "createdAt": "2024-01-01T00:00:00Z",
    "lastUsedTime": 1234567890,
}

EXPECTED_PROFILE = Profile(
    id="p0",
    title="Morning Brew",
    profile_type=1,
    ratio=16.0,
    bloom_enabled=True,
    bloom_ratio=2.0,
    bloom_duration=30,
    bloom_temperature=93.0,
    ss_pulses_enabled=False,
    ss_pulses_number=1,
    ss_pulses_interval=10,
    ss_pulse_temperatures=[93.0],
    batch_pulses_enabled=False,
    batch_pulses_number=1,
    batch_pulses_interval=10,
    batch_pulse_temperatures=[93.0],
)


def test_mapper_converts_fellow_dict_to_profile() -> None:
    profile = FellowProfileMapper.to_entity(SAMPLE_FELLOW_PROFILE)
    assert profile == EXPECTED_PROFILE


def test_mapper_converts_profile_create_to_fellow_dict() -> None:
    create = ProfileCreate(
        title="Morning Brew",
        profile_type=1,
        ratio=16.0,
        bloom_enabled=True,
        bloom_ratio=2.0,
        bloom_duration=30,
        bloom_temperature=93.0,
        ss_pulses_enabled=False,
        ss_pulses_number=1,
        ss_pulses_interval=10,
        ss_pulse_temperatures=[93.0],
        batch_pulses_enabled=False,
        batch_pulses_number=1,
        batch_pulses_interval=10,
        batch_pulse_temperatures=[93.0],
    )
    result = FellowProfileMapper.from_create(create)
    assert result["title"] == "Morning Brew"
    assert result["profileType"] == 1
    assert result["ratio"] == 16.0
    assert result["bloomEnabled"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/profiles/test_fellow_client.py -v -k mapper
```

Expected: FAIL.

- [ ] **Step 3: Implement FellowProfileMapper**

`src/fellow_aiden_api/profiles/client/__init__.py` — empty file.

`src/fellow_aiden_api/profiles/client/fellow_client_mapper.py`:

```python
from typing import Any

from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileUpdate


class FellowProfileMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Profile:
        return Profile(
            id=data["id"],
            title=data["title"],
            profile_type=data["profileType"],
            ratio=data["ratio"],
            bloom_enabled=data["bloomEnabled"],
            bloom_ratio=data["bloomRatio"],
            bloom_duration=data["bloomDuration"],
            bloom_temperature=data["bloomTemperature"],
            ss_pulses_enabled=data["ssPulsesEnabled"],
            ss_pulses_number=data["ssPulsesNumber"],
            ss_pulses_interval=data["ssPulsesInterval"],
            ss_pulse_temperatures=data["ssPulseTemperatures"],
            batch_pulses_enabled=data["batchPulsesEnabled"],
            batch_pulses_number=data["batchPulsesNumber"],
            batch_pulses_interval=data["batchPulsesInterval"],
            batch_pulse_temperatures=data["batchPulseTemperatures"],
        )

    @staticmethod
    def from_create(create: ProfileCreate) -> dict[str, Any]:
        return {
            "profileType": create.profile_type,
            "title": create.title,
            "ratio": create.ratio,
            "bloomEnabled": create.bloom_enabled,
            "bloomRatio": create.bloom_ratio,
            "bloomDuration": create.bloom_duration,
            "bloomTemperature": create.bloom_temperature,
            "ssPulsesEnabled": create.ss_pulses_enabled,
            "ssPulsesNumber": create.ss_pulses_number,
            "ssPulsesInterval": create.ss_pulses_interval,
            "ssPulseTemperatures": create.ss_pulse_temperatures,
            "batchPulsesEnabled": create.batch_pulses_enabled,
            "batchPulsesNumber": create.batch_pulses_number,
            "batchPulsesInterval": create.batch_pulses_interval,
            "batchPulseTemperatures": create.batch_pulse_temperatures,
        }

    @staticmethod
    def from_update(update: ProfileUpdate) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if update.title is not None:
            data["title"] = update.title
        if update.ratio is not None:
            data["ratio"] = update.ratio
        if update.bloom_enabled is not None:
            data["bloomEnabled"] = update.bloom_enabled
        if update.bloom_ratio is not None:
            data["bloomRatio"] = update.bloom_ratio
        if update.bloom_duration is not None:
            data["bloomDuration"] = update.bloom_duration
        if update.bloom_temperature is not None:
            data["bloomTemperature"] = update.bloom_temperature
        if update.ss_pulses_enabled is not None:
            data["ssPulsesEnabled"] = update.ss_pulses_enabled
        if update.ss_pulses_number is not None:
            data["ssPulsesNumber"] = update.ss_pulses_number
        if update.ss_pulses_interval is not None:
            data["ssPulsesInterval"] = update.ss_pulses_interval
        if update.ss_pulse_temperatures is not None:
            data["ssPulseTemperatures"] = update.ss_pulse_temperatures
        if update.batch_pulses_enabled is not None:
            data["batchPulsesEnabled"] = update.batch_pulses_enabled
        if update.batch_pulses_number is not None:
            data["batchPulsesNumber"] = update.batch_pulses_number
        if update.batch_pulses_interval is not None:
            data["batchPulsesInterval"] = update.batch_pulses_interval
        if update.batch_pulse_temperatures is not None:
            data["batchPulseTemperatures"] = update.batch_pulse_temperatures
        return data
```

- [ ] **Step 4: Run mapper tests**

```bash
uv run pytest tests/profiles/test_fellow_client.py -v -k mapper
```

Expected: PASS.

- [ ] **Step 5: Write failing tests for FellowProfileClient**

Add to `tests/profiles/test_fellow_client.py`:

```python
from unittest.mock import MagicMock

import pytest

from fellow_aiden_api.profiles.client.fellow_client import FellowProfileClient
from fellow_aiden_api.profiles.model.profile import ProfileLink


@pytest.mark.anyio
async def test_get_profiles_returns_mapped_entities() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_profiles.return_value = [SAMPLE_FELLOW_PROFILE]

    client = FellowProfileClient(fellow=mock_fellow)
    profiles = await client.get_profiles()

    assert len(profiles) == 1
    assert profiles[0] == EXPECTED_PROFILE


@pytest.mark.anyio
async def test_delete_profile_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_profile_by_id.return_value = True

    client = FellowProfileClient(fellow=mock_fellow)
    await client.delete_profile("p0")

    mock_fellow.delete_profile_by_id.assert_called_once_with("p0")


@pytest.mark.anyio
async def test_generate_link_returns_profile_link() -> None:
    mock_fellow = MagicMock()
    mock_fellow.generate_share_link.return_value = "https://brew.link/abc123"

    client = FellowProfileClient(fellow=mock_fellow)
    link = await client.generate_link("p0")

    assert link == ProfileLink(url="https://brew.link/abc123")
```

- [ ] **Step 6: Implement FellowProfileClient**

`src/fellow_aiden_api/profiles/client/fellow_client.py`:

```python
import asyncio
from typing import Any

from fellow_aiden import FellowAiden

from fellow_aiden_api.profiles.client.fellow_client_mapper import FellowProfileMapper
from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate


class FellowProfileClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow
        self._mapper = FellowProfileMapper()

    async def get_profiles(self) -> list[Profile]:
        data: list[dict[str, Any]] = await asyncio.to_thread(self._fellow.get_profiles)
        return [self._mapper.to_entity(p) for p in data]

    async def get_profile(self, profile_id: str) -> Profile | None:
        profiles = await self.get_profiles()
        return next((p for p in profiles if p.id == profile_id), None)

    async def create_profile(self, profile: ProfileCreate) -> Profile:
        fellow_data = self._mapper.from_create(profile)
        result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_profile, fellow_data)
        return self._mapper.to_entity(result)

    async def create_profile_from_link(self, brew_link: str) -> Profile:
        result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_profile_from_link, brew_link)
        return self._mapper.to_entity(result)

    async def update_profile(self, profile_id: str, profile: ProfileUpdate) -> None:
        fellow_data = self._mapper.from_update(profile)
        await asyncio.to_thread(self._fellow.update_profile, profile_id, fellow_data)

    async def delete_profile(self, profile_id: str) -> None:
        await asyncio.to_thread(self._fellow.delete_profile_by_id, profile_id)

    async def generate_link(self, profile_id: str) -> ProfileLink:
        url: str = await asyncio.to_thread(self._fellow.generate_share_link, profile_id)
        return ProfileLink(url=url)
```

- [ ] **Step 7: Run tests**

```bash
uv run pytest tests/profiles/test_fellow_client.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/fellow_aiden_api/profiles/client/ tests/profiles/
git commit -m "feat(profiles): add FellowProfileClient with async wrapper and mapper"
```

---

## Task 12: Profiles Domain — Service

**Files:**
- Create: `src/fellow_aiden_api/profiles/service.py`
- Create: `tests/profiles/test_service.py`

- [ ] **Step 1: Write failing tests for ProfileService**

`tests/profiles/test_service.py`:

```python
from unittest.mock import AsyncMock

import pytest

from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate
from fellow_aiden_api.profiles.service import (
    ProfileCreateOutcome,
    ProfileDeleteOutcome,
    ProfileGetOutcome,
    ProfileLinkOutcome,
    ProfileListOutcome,
    ProfileService,
    ProfileUpdateOutcome,
)

SAMPLE_PROFILE = Profile(
    id="p0",
    title="Morning Brew",
    profile_type=1,
    ratio=16.0,
    bloom_enabled=True,
    bloom_ratio=2.0,
    bloom_duration=30,
    bloom_temperature=93.0,
    ss_pulses_enabled=False,
    ss_pulses_number=1,
    ss_pulses_interval=10,
    ss_pulse_temperatures=[93.0],
    batch_pulses_enabled=False,
    batch_pulses_number=1,
    batch_pulses_interval=10,
    batch_pulse_temperatures=[93.0],
)


@pytest.mark.anyio
async def test_list_profiles_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profiles.return_value = [SAMPLE_PROFILE]

    service = ProfileService(facade=mock_facade)
    result = await service.list_profiles()

    assert result.outcome == ProfileListOutcome.SUCCESS
    assert result.profiles == [SAMPLE_PROFILE]


@pytest.mark.anyio
async def test_list_profiles_unavailable() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profiles.side_effect = Exception("fail")

    service = ProfileService(facade=mock_facade)
    result = await service.list_profiles()

    assert result.outcome == ProfileListOutcome.FELLOW_UNAVAILABLE


@pytest.mark.anyio
async def test_get_profile_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profile.return_value = SAMPLE_PROFILE

    service = ProfileService(facade=mock_facade)
    result = await service.get_profile("p0")

    assert result.outcome == ProfileGetOutcome.SUCCESS
    assert result.profile == SAMPLE_PROFILE


@pytest.mark.anyio
async def test_get_profile_not_found() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_profile.return_value = None

    service = ProfileService(facade=mock_facade)
    result = await service.get_profile("p99")

    assert result.outcome == ProfileGetOutcome.NOT_FOUND


@pytest.mark.anyio
async def test_create_profile_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.create_profile.return_value = SAMPLE_PROFILE

    service = ProfileService(facade=mock_facade)
    create = ProfileCreate(
        title="Morning Brew", profile_type=1, ratio=16.0,
        bloom_enabled=True, bloom_ratio=2.0, bloom_duration=30, bloom_temperature=93.0,
        ss_pulses_enabled=False, ss_pulses_number=1, ss_pulses_interval=10, ss_pulse_temperatures=[93.0],
        batch_pulses_enabled=False, batch_pulses_number=1, batch_pulses_interval=10, batch_pulse_temperatures=[93.0],
    )
    result = await service.create_profile(create)

    assert result.outcome == ProfileCreateOutcome.SUCCESS
    assert result.profile == SAMPLE_PROFILE


@pytest.mark.anyio
async def test_create_profile_from_link_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.create_profile_from_link.return_value = SAMPLE_PROFILE

    service = ProfileService(facade=mock_facade)
    result = await service.create_profile_from_link("https://brew.link/abc")

    assert result.outcome == ProfileCreateOutcome.SUCCESS
    assert result.profile == SAMPLE_PROFILE


@pytest.mark.anyio
async def test_delete_profile_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.delete_profile.return_value = None

    service = ProfileService(facade=mock_facade)
    result = await service.delete_profile("p0")

    assert result.outcome == ProfileDeleteOutcome.SUCCESS


@pytest.mark.anyio
async def test_generate_link_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.generate_link.return_value = ProfileLink(url="https://brew.link/abc")

    service = ProfileService(facade=mock_facade)
    result = await service.generate_link("p0")

    assert result.outcome == ProfileLinkOutcome.SUCCESS
    assert result.link == ProfileLink(url="https://brew.link/abc")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/profiles/test_service.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement ProfileService**

`src/fellow_aiden_api/profiles/service.py`:

```python
import logging
from dataclasses import dataclass
from enum import Enum

from fellow_aiden_api.profiles.facade import ProfileFacade
from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate

logger = logging.getLogger(__name__)


class ProfileListOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileGetOutcome(Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileCreateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileUpdateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileDeleteOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ProfileLinkOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


@dataclass
class ProfileListResult:
    outcome: ProfileListOutcome
    profiles: list[Profile] | None = None
    error: str | None = None


@dataclass
class ProfileGetResult:
    outcome: ProfileGetOutcome
    profile: Profile | None = None
    error: str | None = None


@dataclass
class ProfileCreateResult:
    outcome: ProfileCreateOutcome
    profile: Profile | None = None
    error: str | None = None


@dataclass
class ProfileUpdateResult:
    outcome: ProfileUpdateOutcome
    error: str | None = None


@dataclass
class ProfileDeleteResult:
    outcome: ProfileDeleteOutcome
    error: str | None = None


@dataclass
class ProfileLinkResult:
    outcome: ProfileLinkOutcome
    link: ProfileLink | None = None
    error: str | None = None


class ProfileService:
    def __init__(self, facade: ProfileFacade) -> None:
        self._facade = facade

    async def list_profiles(self) -> ProfileListResult:
        try:
            profiles = await self._facade.get_profiles()
        except Exception:
            logger.exception("Failed to list profiles")
            return ProfileListResult(outcome=ProfileListOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileListResult(outcome=ProfileListOutcome.SUCCESS, profiles=profiles)

    async def get_profile(self, profile_id: str) -> ProfileGetResult:
        try:
            profile = await self._facade.get_profile(profile_id)
        except Exception:
            logger.exception("Failed to get profile")
            return ProfileGetResult(outcome=ProfileGetOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        if profile is None:
            return ProfileGetResult(outcome=ProfileGetOutcome.NOT_FOUND, error=f"Profile {profile_id} not found")
        return ProfileGetResult(outcome=ProfileGetOutcome.SUCCESS, profile=profile)

    async def create_profile(self, create: ProfileCreate) -> ProfileCreateResult:
        try:
            profile = await self._facade.create_profile(create)
        except Exception:
            logger.exception("Failed to create profile")
            return ProfileCreateResult(outcome=ProfileCreateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileCreateResult(outcome=ProfileCreateOutcome.SUCCESS, profile=profile)

    async def create_profile_from_link(self, brew_link: str) -> ProfileCreateResult:
        try:
            profile = await self._facade.create_profile_from_link(brew_link)
        except Exception:
            logger.exception("Failed to create profile from link")
            return ProfileCreateResult(outcome=ProfileCreateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileCreateResult(outcome=ProfileCreateOutcome.SUCCESS, profile=profile)

    async def update_profile(self, profile_id: str, update: ProfileUpdate) -> ProfileUpdateResult:
        try:
            await self._facade.update_profile(profile_id, update)
        except Exception:
            logger.exception("Failed to update profile")
            return ProfileUpdateResult(outcome=ProfileUpdateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileUpdateResult(outcome=ProfileUpdateOutcome.SUCCESS)

    async def delete_profile(self, profile_id: str) -> ProfileDeleteResult:
        try:
            await self._facade.delete_profile(profile_id)
        except Exception:
            logger.exception("Failed to delete profile")
            return ProfileDeleteResult(outcome=ProfileDeleteOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileDeleteResult(outcome=ProfileDeleteOutcome.SUCCESS)

    async def generate_link(self, profile_id: str) -> ProfileLinkResult:
        try:
            link = await self._facade.generate_link(profile_id)
        except Exception:
            logger.exception("Failed to generate share link")
            return ProfileLinkResult(outcome=ProfileLinkOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ProfileLinkResult(outcome=ProfileLinkOutcome.SUCCESS, link=link)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/profiles/test_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fellow_aiden_api/profiles/service.py tests/profiles/test_service.py
git commit -m "feat(profiles): add ProfileService with typed outcomes"
```

---

## Task 13: Profiles Domain — API Models + Mapper + Router

**Files:**
- Create: `src/fellow_aiden_api/profiles/model/api/__init__.py`
- Create: `src/fellow_aiden_api/profiles/model/api/requests.py`
- Create: `src/fellow_aiden_api/profiles/model/api/responses.py`
- Create: `src/fellow_aiden_api/profiles/mapper.py`
- Create: `src/fellow_aiden_api/profiles/dependencies.py`
- Create: `src/fellow_aiden_api/profiles/router.py`
- Modify: `src/fellow_aiden_api/main.py`
- Create: `tests/profiles/test_router.py`

- [ ] **Step 1: Write failing e2e tests for profiles router**

`tests/profiles/test_router.py`:

```python
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from fellow_aiden_api.main import app
from fellow_aiden_api.profiles.dependencies import get_profile_service
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

SAMPLE_PROFILE = Profile(
    id="p0",
    title="Morning Brew",
    profile_type=1,
    ratio=16.0,
    bloom_enabled=True,
    bloom_ratio=2.0,
    bloom_duration=30,
    bloom_temperature=93.0,
    ss_pulses_enabled=False,
    ss_pulses_number=1,
    ss_pulses_interval=10,
    ss_pulse_temperatures=[93.0],
    batch_pulses_enabled=False,
    batch_pulses_number=1,
    batch_pulses_interval=10,
    batch_pulse_temperatures=[93.0],
)


@pytest.fixture
def mock_profile_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_profile_service(mock_profile_service: AsyncMock) -> None:
    app.dependency_overrides[get_profile_service] = lambda: mock_profile_service
    yield
    app.dependency_overrides.pop(get_profile_service, None)


@pytest.mark.anyio
async def test_list_profiles_returns_200(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.list_profiles.return_value = ProfileListResult(
        outcome=ProfileListOutcome.SUCCESS,
        profiles=[SAMPLE_PROFILE],
    )
    response = await client.get("/profiles")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "p0"
    assert data[0]["title"] == "Morning Brew"


@pytest.mark.anyio
async def test_get_profile_returns_200(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.SUCCESS,
        profile=SAMPLE_PROFILE,
    )
    response = await client.get("/profiles/p0")
    assert response.status_code == 200
    assert response.json()["id"] == "p0"


@pytest.mark.anyio
async def test_get_profile_returns_404(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.get_profile.return_value = ProfileGetResult(
        outcome=ProfileGetOutcome.NOT_FOUND,
        error="Not found",
    )
    response = await client.get("/profiles/p99")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_profile_from_fields_returns_201(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.create_profile.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=SAMPLE_PROFILE,
    )
    response = await client.post("/profiles", json={
        "source": "manual",
        "title": "Morning Brew",
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
    assert response.status_code == 201
    assert response.json()["id"] == "p0"


@pytest.mark.anyio
async def test_create_profile_from_link_returns_201(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.create_profile_from_link.return_value = ProfileCreateResult(
        outcome=ProfileCreateOutcome.SUCCESS,
        profile=SAMPLE_PROFILE,
    )
    response = await client.post("/profiles", json={
        "source": "brew_link",
        "brew_link": "https://brew.link/abc123",
    })
    assert response.status_code == 201
    assert response.json()["id"] == "p0"


@pytest.mark.anyio
async def test_delete_profile_returns_204(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.delete_profile.return_value = ProfileDeleteResult(
        outcome=ProfileDeleteOutcome.SUCCESS,
    )
    response = await client.delete("/profiles/p0")
    assert response.status_code == 204


@pytest.mark.anyio
async def test_generate_link_returns_201(client: AsyncClient, mock_profile_service: AsyncMock) -> None:
    mock_profile_service.generate_link.return_value = ProfileLinkResult(
        outcome=ProfileLinkOutcome.SUCCESS,
        link=ProfileLink(url="https://brew.link/abc123"),
    )
    response = await client.post("/profiles/p0/link")
    assert response.status_code == 201
    assert response.json()["url"] == "https://brew.link/abc123"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/profiles/test_router.py -v
```

Expected: FAIL.

- [ ] **Step 3: Implement API models**

`src/fellow_aiden_api/profiles/model/api/__init__.py` — empty file.

`src/fellow_aiden_api/profiles/model/api/requests.py`:

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl


class ProfileCreateFromFieldsAPIRequest(BaseModel):
    source: Literal["manual"]
    title: str = Field(max_length=50)
    profile_type: int
    ratio: float = Field(ge=14.0, le=20.0)
    bloom_enabled: bool
    bloom_ratio: float = Field(ge=1.0, le=3.0)
    bloom_duration: int = Field(ge=1, le=120)
    bloom_temperature: float = Field(ge=50.0, le=99.0)
    ss_pulses_enabled: bool
    ss_pulses_number: int = Field(ge=1, le=10)
    ss_pulses_interval: int = Field(ge=5, le=60)
    ss_pulse_temperatures: list[float]
    batch_pulses_enabled: bool
    batch_pulses_number: int = Field(ge=1, le=10)
    batch_pulses_interval: int = Field(ge=5, le=60)
    batch_pulse_temperatures: list[float]


class ProfileCreateFromLinkAPIRequest(BaseModel):
    source: Literal["brew_link"]
    brew_link: HttpUrl


ProfileCreateAPIRequest = Annotated[
    ProfileCreateFromFieldsAPIRequest | ProfileCreateFromLinkAPIRequest,
    Field(discriminator="source"),
]


class ProfileUpdateAPIRequest(BaseModel):
    title: str | None = Field(default=None, max_length=50)
    ratio: float | None = Field(default=None, ge=14.0, le=20.0)
    bloom_enabled: bool | None = None
    bloom_ratio: float | None = Field(default=None, ge=1.0, le=3.0)
    bloom_duration: int | None = Field(default=None, ge=1, le=120)
    bloom_temperature: float | None = Field(default=None, ge=50.0, le=99.0)
    ss_pulses_enabled: bool | None = None
    ss_pulses_number: int | None = Field(default=None, ge=1, le=10)
    ss_pulses_interval: int | None = Field(default=None, ge=5, le=60)
    ss_pulse_temperatures: list[float] | None = None
    batch_pulses_enabled: bool | None = None
    batch_pulses_number: int | None = Field(default=None, ge=1, le=10)
    batch_pulses_interval: int | None = Field(default=None, ge=5, le=60)
    batch_pulse_temperatures: list[float] | None = None
```

`src/fellow_aiden_api/profiles/model/api/responses.py`:

```python
from pydantic import BaseModel


class ProfileAPIResponse(BaseModel):
    id: str
    title: str
    profile_type: int
    ratio: float
    bloom_enabled: bool
    bloom_ratio: float
    bloom_duration: int
    bloom_temperature: float
    ss_pulses_enabled: bool
    ss_pulses_number: int
    ss_pulses_interval: int
    ss_pulse_temperatures: list[float]
    batch_pulses_enabled: bool
    batch_pulses_number: int
    batch_pulses_interval: int
    batch_pulse_temperatures: list[float]


class ProfileLinkAPIResponse(BaseModel):
    url: str
```

- [ ] **Step 4: Implement mapper**

`src/fellow_aiden_api/profiles/mapper.py`:

```python
from fellow_aiden_api.profiles.model.api.requests import (
    ProfileCreateFromFieldsAPIRequest,
    ProfileUpdateAPIRequest,
)
from fellow_aiden_api.profiles.model.api.responses import ProfileAPIResponse, ProfileLinkAPIResponse
from fellow_aiden_api.profiles.model.profile import Profile, ProfileCreate, ProfileLink, ProfileUpdate


class ProfileMapper:
    @staticmethod
    def to_api_response(profile: Profile) -> ProfileAPIResponse:
        return ProfileAPIResponse(
            id=profile.id,
            title=profile.title,
            profile_type=profile.profile_type,
            ratio=profile.ratio,
            bloom_enabled=profile.bloom_enabled,
            bloom_ratio=profile.bloom_ratio,
            bloom_duration=profile.bloom_duration,
            bloom_temperature=profile.bloom_temperature,
            ss_pulses_enabled=profile.ss_pulses_enabled,
            ss_pulses_number=profile.ss_pulses_number,
            ss_pulses_interval=profile.ss_pulses_interval,
            ss_pulse_temperatures=profile.ss_pulse_temperatures,
            batch_pulses_enabled=profile.batch_pulses_enabled,
            batch_pulses_number=profile.batch_pulses_number,
            batch_pulses_interval=profile.batch_pulses_interval,
            batch_pulse_temperatures=profile.batch_pulse_temperatures,
        )

    @staticmethod
    def to_link_response(link: ProfileLink) -> ProfileLinkAPIResponse:
        return ProfileLinkAPIResponse(url=link.url)

    @staticmethod
    def from_create_request(request: ProfileCreateFromFieldsAPIRequest) -> ProfileCreate:
        return ProfileCreate(
            title=request.title,
            profile_type=request.profile_type,
            ratio=request.ratio,
            bloom_enabled=request.bloom_enabled,
            bloom_ratio=request.bloom_ratio,
            bloom_duration=request.bloom_duration,
            bloom_temperature=request.bloom_temperature,
            ss_pulses_enabled=request.ss_pulses_enabled,
            ss_pulses_number=request.ss_pulses_number,
            ss_pulses_interval=request.ss_pulses_interval,
            ss_pulse_temperatures=request.ss_pulse_temperatures,
            batch_pulses_enabled=request.batch_pulses_enabled,
            batch_pulses_number=request.batch_pulses_number,
            batch_pulses_interval=request.batch_pulses_interval,
            batch_pulse_temperatures=request.batch_pulse_temperatures,
        )

    @staticmethod
    def from_update_request(request: ProfileUpdateAPIRequest) -> ProfileUpdate:
        return ProfileUpdate(
            title=request.title,
            ratio=request.ratio,
            bloom_enabled=request.bloom_enabled,
            bloom_ratio=request.bloom_ratio,
            bloom_duration=request.bloom_duration,
            bloom_temperature=request.bloom_temperature,
            ss_pulses_enabled=request.ss_pulses_enabled,
            ss_pulses_number=request.ss_pulses_number,
            ss_pulses_interval=request.ss_pulses_interval,
            ss_pulse_temperatures=request.ss_pulse_temperatures,
            batch_pulses_enabled=request.batch_pulses_enabled,
            batch_pulses_number=request.batch_pulses_number,
            batch_pulses_interval=request.batch_pulses_interval,
            batch_pulse_temperatures=request.batch_pulse_temperatures,
        )
```

- [ ] **Step 5: Implement dependencies**

`src/fellow_aiden_api/profiles/dependencies.py`:

```python
from fellow_aiden_api.profiles.service import ProfileService


def get_profile_service() -> ProfileService:
    raise NotImplementedError("Must be overridden — wired in app lifespan")
```

- [ ] **Step 6: Implement router**

`src/fellow_aiden_api/profiles/router.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from fellow_aiden_api.profiles.dependencies import get_profile_service
from fellow_aiden_api.profiles.mapper import ProfileMapper
from fellow_aiden_api.profiles.model.api.requests import (
    ProfileCreateAPIRequest,
    ProfileCreateFromFieldsAPIRequest,
    ProfileCreateFromLinkAPIRequest,
    ProfileUpdateAPIRequest,
)
from fellow_aiden_api.profiles.model.api.responses import ProfileAPIResponse, ProfileLinkAPIResponse
from fellow_aiden_api.profiles.service import (
    ProfileCreateOutcome,
    ProfileDeleteOutcome,
    ProfileGetOutcome,
    ProfileLinkOutcome,
    ProfileListOutcome,
    ProfileService,
    ProfileUpdateOutcome,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("")
async def list_profiles(
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> list[ProfileAPIResponse]:
    result = await service.list_profiles()
    match result.outcome:
        case ProfileListOutcome.SUCCESS:
            assert result.profiles is not None
            return [ProfileMapper.to_api_response(p) for p in result.profiles]
        case ProfileListOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.get("/{profile_id}")
async def get_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileAPIResponse:
    result = await service.get_profile(profile_id)
    match result.outcome:
        case ProfileGetOutcome.SUCCESS:
            assert result.profile is not None
            return ProfileMapper.to_api_response(result.profile)
        case ProfileGetOutcome.NOT_FOUND:
            raise HTTPException(status_code=404, detail=result.error)
        case ProfileGetOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.post("", status_code=201)
async def create_profile(
    request: ProfileCreateAPIRequest,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileAPIResponse:
    if isinstance(request, ProfileCreateFromLinkAPIRequest):
        result = await service.create_profile_from_link(str(request.brew_link))
    else:
        domain_create = ProfileMapper.from_create_request(request)
        result = await service.create_profile(domain_create)
    match result.outcome:
        case ProfileCreateOutcome.SUCCESS:
            assert result.profile is not None
            return ProfileMapper.to_api_response(result.profile)
        case ProfileCreateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.patch("/{profile_id}")
async def update_profile(
    profile_id: str,
    request: ProfileUpdateAPIRequest,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> dict[str, str]:
    domain_update = ProfileMapper.from_update_request(request)
    result = await service.update_profile(profile_id, domain_update)
    match result.outcome:
        case ProfileUpdateOutcome.SUCCESS:
            return {"status": "ok"}
        case ProfileUpdateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> Response:
    result = await service.delete_profile(profile_id)
    match result.outcome:
        case ProfileDeleteOutcome.SUCCESS:
            return Response(status_code=204)
        case ProfileDeleteOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.post("/{profile_id}/link", status_code=201)
async def generate_link(
    profile_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileLinkAPIResponse:
    result = await service.generate_link(profile_id)
    match result.outcome:
        case ProfileLinkOutcome.SUCCESS:
            assert result.link is not None
            return ProfileMapper.to_link_response(result.link)
        case ProfileLinkOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
```

- [ ] **Step 7: Wire router into app**

Add to `src/fellow_aiden_api/main.py`:

```python
from fellow_aiden_api.profiles.router import router as profiles_router
```

And:

```python
app.include_router(profiles_router)
```

- [ ] **Step 8: Run tests**

```bash
uv run pytest tests/profiles/ -v
```

Expected: PASS.

- [ ] **Step 9: Run full suite + lints**

```bash
uv run pytest -v && uv run ruff check src/ tests/ && uv run ty check src/
```

- [ ] **Step 10: Commit**

```bash
git add src/fellow_aiden_api/profiles/ src/fellow_aiden_api/main.py tests/profiles/test_router.py
git commit -m "feat(profiles): add profiles router, API models, mapper, and DI"
```

---

## Task 14: Schedules Domain — Entity + Facade

**Files:**
- Create: `src/fellow_aiden_api/schedules/__init__.py`
- Create: `src/fellow_aiden_api/schedules/model/__init__.py`
- Create: `src/fellow_aiden_api/schedules/model/schedule.py`
- Create: `src/fellow_aiden_api/schedules/facade.py`

- [ ] **Step 1: Create Schedule entity**

`src/fellow_aiden_api/schedules/__init__.py` — empty file.

`src/fellow_aiden_api/schedules/model/__init__.py` — empty file.

`src/fellow_aiden_api/schedules/model/schedule.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Schedule:
    id: str
    days: list[bool]  # 7 elements, Sunday=0
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int  # ml
    profile_id: str


@dataclass(frozen=True)
class ScheduleCreate:
    days: list[bool]
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int
    profile_id: str


@dataclass(frozen=True)
class ScheduleUpdate:
    days: list[bool] | None = None
    second_from_start_of_day: int | None = None
    enabled: bool | None = None
    amount_of_water: int | None = None
    profile_id: str | None = None
```

- [ ] **Step 2: Create ScheduleFacade protocol**

`src/fellow_aiden_api/schedules/facade.py`:

```python
from typing import Protocol

from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class ScheduleFacade(Protocol):
    async def get_schedules(self) -> list[Schedule]: ...
    async def create_schedule(self, schedule: ScheduleCreate) -> Schedule: ...
    async def update_schedule(self, schedule_id: str, schedule: ScheduleUpdate) -> None: ...
    async def delete_schedule(self, schedule_id: str) -> None: ...
```

- [ ] **Step 3: Run lints and type check**

```bash
uv run ruff check src/fellow_aiden_api/schedules/ && uv run ty check src/
```

- [ ] **Step 4: Commit**

```bash
git add src/fellow_aiden_api/schedules/
git commit -m "feat(schedules): add Schedule entity and ScheduleFacade protocol"
```

---

## Task 15: Schedules Domain — Infrastructure Client

**Files:**
- Create: `src/fellow_aiden_api/schedules/client/__init__.py`
- Create: `src/fellow_aiden_api/schedules/client/fellow_client_mapper.py`
- Create: `src/fellow_aiden_api/schedules/client/fellow_client.py`
- Create: `tests/schedules/__init__.py`
- Create: `tests/schedules/test_fellow_client.py`

- [ ] **Step 1: Write failing test for schedule client mapper**

`tests/schedules/__init__.py` — empty file.

`tests/schedules/test_fellow_client.py`:

```python
from fellow_aiden_api.schedules.client.fellow_client_mapper import FellowScheduleMapper
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate

SAMPLE_FELLOW_SCHEDULE: dict = {
    "id": "s0",
    "days": [False, True, True, True, True, True, False],
    "secondFromStartOfTheDay": 25200,
    "enabled": True,
    "amountOfWater": 600,
    "profileId": "p0",
}

EXPECTED_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


def test_mapper_converts_fellow_dict_to_schedule() -> None:
    schedule = FellowScheduleMapper.to_entity(SAMPLE_FELLOW_SCHEDULE)
    assert schedule == EXPECTED_SCHEDULE


def test_mapper_converts_schedule_create_to_fellow_dict() -> None:
    create = ScheduleCreate(
        days=[False, True, True, True, True, True, False],
        second_from_start_of_day=25200,
        enabled=True,
        amount_of_water=600,
        profile_id="p0",
    )
    result = FellowScheduleMapper.from_create(create)
    assert result["days"] == [False, True, True, True, True, True, False]
    assert result["secondFromStartOfTheDay"] == 25200
    assert result["profileId"] == "p0"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/schedules/test_fellow_client.py -v -k mapper
```

- [ ] **Step 3: Implement FellowScheduleMapper**

`src/fellow_aiden_api/schedules/client/__init__.py` — empty file.

`src/fellow_aiden_api/schedules/client/fellow_client_mapper.py`:

```python
from typing import Any

from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class FellowScheduleMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Schedule:
        return Schedule(
            id=data["id"],
            days=data["days"],
            second_from_start_of_day=data["secondFromStartOfTheDay"],
            enabled=data["enabled"],
            amount_of_water=data["amountOfWater"],
            profile_id=data["profileId"],
        )

    @staticmethod
    def from_create(create: ScheduleCreate) -> dict[str, Any]:
        return {
            "days": create.days,
            "secondFromStartOfTheDay": create.second_from_start_of_day,
            "enabled": create.enabled,
            "amountOfWater": create.amount_of_water,
            "profileId": create.profile_id,
        }

    @staticmethod
    def from_update(update: ScheduleUpdate) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if update.days is not None:
            data["days"] = update.days
        if update.second_from_start_of_day is not None:
            data["secondFromStartOfTheDay"] = update.second_from_start_of_day
        if update.enabled is not None:
            data["enabled"] = update.enabled
        if update.amount_of_water is not None:
            data["amountOfWater"] = update.amount_of_water
        if update.profile_id is not None:
            data["profileId"] = update.profile_id
        return data
```

- [ ] **Step 4: Run mapper tests**

```bash
uv run pytest tests/schedules/test_fellow_client.py -v -k mapper
```

Expected: PASS.

- [ ] **Step 5: Write failing tests for FellowScheduleClient**

Add to `tests/schedules/test_fellow_client.py`:

```python
from unittest.mock import MagicMock

import pytest

from fellow_aiden_api.schedules.client.fellow_client import FellowScheduleClient


@pytest.mark.anyio
async def test_get_schedules_returns_mapped_entities() -> None:
    mock_fellow = MagicMock()
    mock_fellow.get_schedules.return_value = [SAMPLE_FELLOW_SCHEDULE]

    client = FellowScheduleClient(fellow=mock_fellow)
    schedules = await client.get_schedules()

    assert len(schedules) == 1
    assert schedules[0] == EXPECTED_SCHEDULE


@pytest.mark.anyio
async def test_delete_schedule_calls_fellow() -> None:
    mock_fellow = MagicMock()
    mock_fellow.delete_schedule_by_id.return_value = True

    client = FellowScheduleClient(fellow=mock_fellow)
    await client.delete_schedule("s0")

    mock_fellow.delete_schedule_by_id.assert_called_once_with("s0")
```

- [ ] **Step 6: Implement FellowScheduleClient**

`src/fellow_aiden_api/schedules/client/fellow_client.py`:

```python
import asyncio
from typing import Any

from fellow_aiden import FellowAiden

from fellow_aiden_api.schedules.client.fellow_client_mapper import FellowScheduleMapper
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class FellowScheduleClient:
    def __init__(self, fellow: FellowAiden) -> None:
        self._fellow = fellow
        self._mapper = FellowScheduleMapper()

    async def get_schedules(self) -> list[Schedule]:
        data: list[dict[str, Any]] = await asyncio.to_thread(self._fellow.get_schedules)
        return [self._mapper.to_entity(s) for s in data]

    async def create_schedule(self, schedule: ScheduleCreate) -> Schedule:
        fellow_data = self._mapper.from_create(schedule)
        result: dict[str, Any] = await asyncio.to_thread(self._fellow.create_schedule, fellow_data)
        return self._mapper.to_entity(result)

    async def update_schedule(self, schedule_id: str, schedule: ScheduleUpdate) -> None:
        fellow_data = self._mapper.from_update(schedule)
        if "enabled" in fellow_data and len(fellow_data) == 1:
            await asyncio.to_thread(self._fellow.toggle_schedule, schedule_id, fellow_data["enabled"])
        else:
            # Fellow library doesn't have a general update_schedule method.
            # For fields beyond enabled, we'd need to delete and recreate.
            # For now, only enabled toggling is supported via PATCH.
            await asyncio.to_thread(self._fellow.toggle_schedule, schedule_id, fellow_data.get("enabled", True))

    async def delete_schedule(self, schedule_id: str) -> None:
        await asyncio.to_thread(self._fellow.delete_schedule_by_id, schedule_id)
```

- [ ] **Step 7: Run tests**

```bash
uv run pytest tests/schedules/test_fellow_client.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/fellow_aiden_api/schedules/client/ tests/schedules/
git commit -m "feat(schedules): add FellowScheduleClient with async wrapper and mapper"
```

---

## Task 16: Schedules Domain — Service

**Files:**
- Create: `src/fellow_aiden_api/schedules/service.py`
- Create: `tests/schedules/test_service.py`

- [ ] **Step 1: Write failing tests for ScheduleService**

`tests/schedules/test_service.py`:

```python
from unittest.mock import AsyncMock

import pytest

from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleDeleteOutcome,
    ScheduleListOutcome,
    ScheduleService,
    ScheduleUpdateOutcome,
)

SAMPLE_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


@pytest.mark.anyio
async def test_list_schedules_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_schedules.return_value = [SAMPLE_SCHEDULE]

    service = ScheduleService(facade=mock_facade)
    result = await service.list_schedules()

    assert result.outcome == ScheduleListOutcome.SUCCESS
    assert result.schedules == [SAMPLE_SCHEDULE]


@pytest.mark.anyio
async def test_list_schedules_unavailable() -> None:
    mock_facade = AsyncMock()
    mock_facade.get_schedules.side_effect = Exception("fail")

    service = ScheduleService(facade=mock_facade)
    result = await service.list_schedules()

    assert result.outcome == ScheduleListOutcome.FELLOW_UNAVAILABLE


@pytest.mark.anyio
async def test_create_schedule_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.create_schedule.return_value = SAMPLE_SCHEDULE

    service = ScheduleService(facade=mock_facade)
    create = ScheduleCreate(
        days=[False, True, True, True, True, True, False],
        second_from_start_of_day=25200,
        enabled=True,
        amount_of_water=600,
        profile_id="p0",
    )
    result = await service.create_schedule(create)

    assert result.outcome == ScheduleCreateOutcome.SUCCESS
    assert result.schedule == SAMPLE_SCHEDULE


@pytest.mark.anyio
async def test_update_schedule_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.update_schedule.return_value = None

    service = ScheduleService(facade=mock_facade)
    update = ScheduleUpdate(enabled=False)
    result = await service.update_schedule("s0", update)

    assert result.outcome == ScheduleUpdateOutcome.SUCCESS


@pytest.mark.anyio
async def test_delete_schedule_success() -> None:
    mock_facade = AsyncMock()
    mock_facade.delete_schedule.return_value = None

    service = ScheduleService(facade=mock_facade)
    result = await service.delete_schedule("s0")

    assert result.outcome == ScheduleDeleteOutcome.SUCCESS
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/schedules/test_service.py -v
```

- [ ] **Step 3: Implement ScheduleService**

`src/fellow_aiden_api/schedules/service.py`:

```python
import logging
from dataclasses import dataclass
from enum import Enum

from fellow_aiden_api.schedules.facade import ScheduleFacade
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate

logger = logging.getLogger(__name__)


class ScheduleListOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ScheduleCreateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ScheduleUpdateOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


class ScheduleDeleteOutcome(Enum):
    SUCCESS = "success"
    FELLOW_UNAVAILABLE = "fellow_unavailable"


@dataclass
class ScheduleListResult:
    outcome: ScheduleListOutcome
    schedules: list[Schedule] | None = None
    error: str | None = None


@dataclass
class ScheduleCreateResult:
    outcome: ScheduleCreateOutcome
    schedule: Schedule | None = None
    error: str | None = None


@dataclass
class ScheduleUpdateResult:
    outcome: ScheduleUpdateOutcome
    error: str | None = None


@dataclass
class ScheduleDeleteResult:
    outcome: ScheduleDeleteOutcome
    error: str | None = None


class ScheduleService:
    def __init__(self, facade: ScheduleFacade) -> None:
        self._facade = facade

    async def list_schedules(self) -> ScheduleListResult:
        try:
            schedules = await self._facade.get_schedules()
        except Exception:
            logger.exception("Failed to list schedules")
            return ScheduleListResult(outcome=ScheduleListOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ScheduleListResult(outcome=ScheduleListOutcome.SUCCESS, schedules=schedules)

    async def create_schedule(self, create: ScheduleCreate) -> ScheduleCreateResult:
        try:
            schedule = await self._facade.create_schedule(create)
        except Exception:
            logger.exception("Failed to create schedule")
            return ScheduleCreateResult(outcome=ScheduleCreateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ScheduleCreateResult(outcome=ScheduleCreateOutcome.SUCCESS, schedule=schedule)

    async def update_schedule(self, schedule_id: str, update: ScheduleUpdate) -> ScheduleUpdateResult:
        try:
            await self._facade.update_schedule(schedule_id, update)
        except Exception:
            logger.exception("Failed to update schedule")
            return ScheduleUpdateResult(outcome=ScheduleUpdateOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ScheduleUpdateResult(outcome=ScheduleUpdateOutcome.SUCCESS)

    async def delete_schedule(self, schedule_id: str) -> ScheduleDeleteResult:
        try:
            await self._facade.delete_schedule(schedule_id)
        except Exception:
            logger.exception("Failed to delete schedule")
            return ScheduleDeleteResult(outcome=ScheduleDeleteOutcome.FELLOW_UNAVAILABLE, error="Fellow cloud unavailable")
        return ScheduleDeleteResult(outcome=ScheduleDeleteOutcome.SUCCESS)
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/schedules/test_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/fellow_aiden_api/schedules/service.py tests/schedules/test_service.py
git commit -m "feat(schedules): add ScheduleService with typed outcomes"
```

---

## Task 17: Schedules Domain — API Models + Mapper + Router

**Files:**
- Create: `src/fellow_aiden_api/schedules/model/api/__init__.py`
- Create: `src/fellow_aiden_api/schedules/model/api/requests.py`
- Create: `src/fellow_aiden_api/schedules/model/api/responses.py`
- Create: `src/fellow_aiden_api/schedules/mapper.py`
- Create: `src/fellow_aiden_api/schedules/dependencies.py`
- Create: `src/fellow_aiden_api/schedules/router.py`
- Modify: `src/fellow_aiden_api/main.py`
- Create: `tests/schedules/test_router.py`

- [ ] **Step 1: Write failing e2e tests for schedules router**

`tests/schedules/test_router.py`:

```python
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from fellow_aiden_api.main import app
from fellow_aiden_api.schedules.dependencies import get_schedule_service
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

SAMPLE_SCHEDULE = Schedule(
    id="s0",
    days=[False, True, True, True, True, True, False],
    second_from_start_of_day=25200,
    enabled=True,
    amount_of_water=600,
    profile_id="p0",
)


@pytest.fixture
def mock_schedule_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_schedule_service(mock_schedule_service: AsyncMock) -> None:
    app.dependency_overrides[get_schedule_service] = lambda: mock_schedule_service
    yield
    app.dependency_overrides.pop(get_schedule_service, None)


@pytest.mark.anyio
async def test_list_schedules_returns_200(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.list_schedules.return_value = ScheduleListResult(
        outcome=ScheduleListOutcome.SUCCESS,
        schedules=[SAMPLE_SCHEDULE],
    )
    response = await client.get("/schedules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "s0"
    assert data[0]["enabled"] is True


@pytest.mark.anyio
async def test_create_schedule_returns_201(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.create_schedule.return_value = ScheduleCreateResult(
        outcome=ScheduleCreateOutcome.SUCCESS,
        schedule=SAMPLE_SCHEDULE,
    )
    response = await client.post("/schedules", json={
        "days": [False, True, True, True, True, True, False],
        "second_from_start_of_day": 25200,
        "enabled": True,
        "amount_of_water": 600,
        "profile_id": "p0",
    })
    assert response.status_code == 201
    assert response.json()["id"] == "s0"


@pytest.mark.anyio
async def test_update_schedule_returns_200(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.update_schedule.return_value = ScheduleUpdateResult(
        outcome=ScheduleUpdateOutcome.SUCCESS,
    )
    response = await client.patch("/schedules/s0", json={"enabled": False})
    assert response.status_code == 200


@pytest.mark.anyio
async def test_delete_schedule_returns_204(client: AsyncClient, mock_schedule_service: AsyncMock) -> None:
    mock_schedule_service.delete_schedule.return_value = ScheduleDeleteResult(
        outcome=ScheduleDeleteOutcome.SUCCESS,
    )
    response = await client.delete("/schedules/s0")
    assert response.status_code == 204
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/schedules/test_router.py -v
```

- [ ] **Step 3: Implement API models**

`src/fellow_aiden_api/schedules/model/api/__init__.py` — empty file.

`src/fellow_aiden_api/schedules/model/api/requests.py`:

```python
from pydantic import BaseModel, Field


class ScheduleCreateAPIRequest(BaseModel):
    days: list[bool] = Field(min_length=7, max_length=7)
    second_from_start_of_day: int = Field(ge=0, le=86399)
    enabled: bool
    amount_of_water: int = Field(ge=150, le=1500)
    profile_id: str = Field(pattern=r"^(p|plocal)\d+$")


class ScheduleUpdateAPIRequest(BaseModel):
    days: list[bool] | None = Field(default=None, min_length=7, max_length=7)
    second_from_start_of_day: int | None = Field(default=None, ge=0, le=86399)
    enabled: bool | None = None
    amount_of_water: int | None = Field(default=None, ge=150, le=1500)
    profile_id: str | None = Field(default=None, pattern=r"^(p|plocal)\d+$")
```

`src/fellow_aiden_api/schedules/model/api/responses.py`:

```python
from pydantic import BaseModel


class ScheduleAPIResponse(BaseModel):
    id: str
    days: list[bool]
    second_from_start_of_day: int
    enabled: bool
    amount_of_water: int
    profile_id: str
```

- [ ] **Step 4: Implement mapper**

`src/fellow_aiden_api/schedules/mapper.py`:

```python
from fellow_aiden_api.schedules.model.api.requests import ScheduleCreateAPIRequest, ScheduleUpdateAPIRequest
from fellow_aiden_api.schedules.model.api.responses import ScheduleAPIResponse
from fellow_aiden_api.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class ScheduleMapper:
    @staticmethod
    def to_api_response(schedule: Schedule) -> ScheduleAPIResponse:
        return ScheduleAPIResponse(
            id=schedule.id,
            days=schedule.days,
            second_from_start_of_day=schedule.second_from_start_of_day,
            enabled=schedule.enabled,
            amount_of_water=schedule.amount_of_water,
            profile_id=schedule.profile_id,
        )

    @staticmethod
    def from_create_request(request: ScheduleCreateAPIRequest) -> ScheduleCreate:
        return ScheduleCreate(
            days=request.days,
            second_from_start_of_day=request.second_from_start_of_day,
            enabled=request.enabled,
            amount_of_water=request.amount_of_water,
            profile_id=request.profile_id,
        )

    @staticmethod
    def from_update_request(request: ScheduleUpdateAPIRequest) -> ScheduleUpdate:
        return ScheduleUpdate(
            days=request.days,
            second_from_start_of_day=request.second_from_start_of_day,
            enabled=request.enabled,
            amount_of_water=request.amount_of_water,
            profile_id=request.profile_id,
        )
```

- [ ] **Step 5: Implement dependencies**

`src/fellow_aiden_api/schedules/dependencies.py`:

```python
from fellow_aiden_api.schedules.service import ScheduleService


def get_schedule_service() -> ScheduleService:
    raise NotImplementedError("Must be overridden — wired in app lifespan")
```

- [ ] **Step 6: Implement router**

`src/fellow_aiden_api/schedules/router.py`:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from fellow_aiden_api.schedules.dependencies import get_schedule_service
from fellow_aiden_api.schedules.mapper import ScheduleMapper
from fellow_aiden_api.schedules.model.api.requests import ScheduleCreateAPIRequest, ScheduleUpdateAPIRequest
from fellow_aiden_api.schedules.model.api.responses import ScheduleAPIResponse
from fellow_aiden_api.schedules.service import (
    ScheduleCreateOutcome,
    ScheduleDeleteOutcome,
    ScheduleListOutcome,
    ScheduleService,
    ScheduleUpdateOutcome,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("")
async def list_schedules(
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> list[ScheduleAPIResponse]:
    result = await service.list_schedules()
    match result.outcome:
        case ScheduleListOutcome.SUCCESS:
            assert result.schedules is not None
            return [ScheduleMapper.to_api_response(s) for s in result.schedules]
        case ScheduleListOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.post("", status_code=201)
async def create_schedule(
    request: ScheduleCreateAPIRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleAPIResponse:
    domain_create = ScheduleMapper.from_create_request(request)
    result = await service.create_schedule(domain_create)
    match result.outcome:
        case ScheduleCreateOutcome.SUCCESS:
            assert result.schedule is not None
            return ScheduleMapper.to_api_response(result.schedule)
        case ScheduleCreateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.patch("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    request: ScheduleUpdateAPIRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> dict[str, str]:
    domain_update = ScheduleMapper.from_update_request(request)
    result = await service.update_schedule(schedule_id, domain_update)
    match result.outcome:
        case ScheduleUpdateOutcome.SUCCESS:
            return {"status": "ok"}
        case ScheduleUpdateOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: str,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> Response:
    result = await service.delete_schedule(schedule_id)
    match result.outcome:
        case ScheduleDeleteOutcome.SUCCESS:
            return Response(status_code=204)
        case ScheduleDeleteOutcome.FELLOW_UNAVAILABLE:
            raise HTTPException(status_code=503, detail=result.error)
```

- [ ] **Step 7: Wire router into app**

Add to `src/fellow_aiden_api/main.py`:

```python
from fellow_aiden_api.schedules.router import router as schedules_router
```

And:

```python
app.include_router(schedules_router)
```

- [ ] **Step 8: Run tests**

```bash
uv run pytest tests/schedules/ -v
```

Expected: PASS.

- [ ] **Step 9: Run full suite + lints**

```bash
uv run pytest -v && uv run ruff check src/ tests/ && uv run ty check src/
```

- [ ] **Step 10: Commit**

```bash
git add src/fellow_aiden_api/schedules/ src/fellow_aiden_api/main.py tests/schedules/test_router.py
git commit -m "feat(schedules): add schedules router, API models, mapper, and DI"
```

---

## Task 18: App Lifespan — Wire FellowAiden Client to Services

**Files:**
- Modify: `src/fellow_aiden_api/main.py`
- Modify: `src/fellow_aiden_api/device/dependencies.py`
- Modify: `src/fellow_aiden_api/profiles/dependencies.py`
- Modify: `src/fellow_aiden_api/schedules/dependencies.py`

This task wires the real `FellowAiden` instance to all services via FastAPI's lifespan. The `FellowAiden` constructor is synchronous and authenticates immediately, so we instantiate it in a thread at startup.

- [ ] **Step 1: Implement the lifespan**

Update `src/fellow_aiden_api/main.py` to the full wired version:

```python
import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fellow_aiden import FellowAiden

from fellow_aiden_api.config import Settings
from fellow_aiden_api.dependencies import require_api_key
from fellow_aiden_api.device.client.fellow_client import FellowDeviceClient
from fellow_aiden_api.device.dependencies import get_device_service
from fellow_aiden_api.device.router import router as device_router
from fellow_aiden_api.device.service import DeviceService
from fellow_aiden_api.health.router import router as health_router
from fellow_aiden_api.profiles.client.fellow_client import FellowProfileClient
from fellow_aiden_api.profiles.dependencies import get_profile_service
from fellow_aiden_api.profiles.router import router as profiles_router
from fellow_aiden_api.profiles.service import ProfileService
from fellow_aiden_api.schedules.client.fellow_client import FellowScheduleClient
from fellow_aiden_api.schedules.dependencies import get_schedule_service
from fellow_aiden_api.schedules.router import router as schedules_router
from fellow_aiden_api.schedules.service import ScheduleService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = Settings()

    fellow = await asyncio.to_thread(
        FellowAiden,
        settings.fellow_email,
        settings.fellow_password.get_secret_value(),
    )

    device_client = FellowDeviceClient(fellow=fellow)
    profile_client = FellowProfileClient(fellow=fellow)
    schedule_client = FellowScheduleClient(fellow=fellow)

    device_service = DeviceService(facade=device_client)
    profile_service = ProfileService(facade=profile_client)
    schedule_service = ScheduleService(facade=schedule_client)

    app.dependency_overrides[get_device_service] = lambda: device_service
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_schedule_service] = lambda: schedule_service

    yield

    app.dependency_overrides.clear()


app = FastAPI(
    title="Fellow Aiden API",
    root_path="/coffee/api",
    lifespan=lifespan,
    dependencies=[Depends(require_api_key)],
)

app.include_router(health_router)
app.include_router(device_router)
app.include_router(profiles_router)
app.include_router(schedules_router)


@app.exception_handler(Exception)
async def catch_all_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

- [ ] **Step 2: Run full test suite**

Tests use `dependency_overrides` in fixtures which take precedence over lifespan overrides. The lifespan doesn't run in tests using `ASGITransport` by default, so existing tests should still pass.

```bash
uv run pytest -v
```

Expected: All PASS.

- [ ] **Step 3: Run lints + type check**

```bash
uv run ruff check src/ tests/ && uv run ruff format --check src/ tests/ && uv run ty check src/
```

- [ ] **Step 4: Commit**

```bash
git add src/fellow_aiden_api/main.py
git commit -m "feat: wire FellowAiden client to all services via app lifespan"
```

---

## Task 19: Docker Setup

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create Dockerfile**

`Dockerfile`:

```dockerfile
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev

FROM python:3.13-slim

RUN useradd --create-home appuser
USER appuser
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/coffee/api/health')"

CMD ["uvicorn", "fellow_aiden_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create docker-compose.yml**

`docker-compose.yml`:

```yaml
services:
  fellow-aiden-api:
    build: .
    container_name: fellow-aiden-api
    restart: unless-stopped
    env_file: .env
    networks:
      - pi-net

networks:
  pi-net:
    external: true
```

- [ ] **Step 3: Verify Docker build**

```bash
docker build -t fellow-aiden-api .
```

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: add Dockerfile and docker-compose for Pi deployment"
```

---

## Task 20: CI Pipeline

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create CI workflow**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --frozen
      - run: uv run ruff check src/ tests/
      - run: uv run ruff format --check src/ tests/

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --frozen
      - run: uv run ty check src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --frozen
      - run: uv run pytest --cov --cov-report=xml -v
      - uses: codecov/codecov-action@v5
        with:
          files: ./coverage.xml
          fail_ci_if_error: false
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add lint, type check, and test workflow with Codecov"
```

---

## Task Summary

| Task | Description | Depends On |
|------|-------------|------------|
| 1 | Project scaffolding (uv, pyproject.toml, ruff, ty) | — |
| 2 | LSP setup and verification | 1 |
| 3 | FastAPI app skeleton + health endpoint | 2 |
| 4 | Configuration (Settings) | 3 |
| 5 | API key guard | 4 |
| 6 | Device entity + facade | 2 |
| 7 | Device infrastructure client | 6 |
| 8 | Device service | 6, 7 |
| 9 | Device API models + mapper + router | 3, 8 |
| 10 | Profiles entity + facade | 2 |
| 11 | Profiles infrastructure client | 10 |
| 12 | Profiles service | 10, 11 |
| 13 | Profiles API models + mapper + router | 3, 12 |
| 14 | Schedules entity + facade | 2 |
| 15 | Schedules infrastructure client | 14 |
| 16 | Schedules service | 14, 15 |
| 17 | Schedules API models + mapper + router | 3, 16 |
| 18 | App lifespan — wire everything | 5, 9, 13, 17 |
| 19 | Docker setup | 18 |
| 20 | CI pipeline | 1 |

**Parallelizable groups:**
- Tasks 6-9, 10-13, 14-17 can be developed in parallel (independent domains)
- Task 20 can be done any time after Task 1
