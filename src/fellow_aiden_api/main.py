import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fellow_aiden import FellowAiden

from fellow_aiden_api.dependencies import get_settings, require_api_key
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
async def _app_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()

    password = settings.fellow_password.get_secret_value()
    fellow = await asyncio.to_thread(FellowAiden, settings.fellow_email, password)

    device_client = FellowDeviceClient(fellow=fellow)
    profile_client = FellowProfileClient(fellow=fellow)
    schedule_client = FellowScheduleClient(fellow=fellow)

    device_service = DeviceService(facade=device_client)
    profile_service = ProfileService(facade=profile_client)
    schedule_service = ScheduleService(facade=schedule_client)

    app.dependency_overrides[get_device_service] = lambda: device_service
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_schedule_service] = lambda: schedule_service

    if _mcp_enabled:
        from fellow_aiden_api.device.mcp import register_device_mcp  # noqa: PLC0415
        from fellow_aiden_api.profiles.mcp import register_profile_mcp  # noqa: PLC0415
        from fellow_aiden_api.schedules.mcp import register_schedule_mcp  # noqa: PLC0415

        register_device_mcp(_mcp_server, device_service)
        register_profile_mcp(_mcp_server, profile_service)
        register_schedule_mcp(_mcp_server, schedule_service)

    yield

    app.dependency_overrides.clear()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    # When MCP is enabled, its sub-app lifespan must run to initialize the session manager.
    if _mcp_enabled:
        async with _mcp_app.lifespan(app), _app_lifespan(app):
            yield
    else:
        async with _app_lifespan(app):
            yield


app = FastAPI(
    title="Fellow Aiden API",
    lifespan=lifespan,
    dependencies=[Depends(require_api_key)],
)

app.include_router(health_router)
app.include_router(device_router)
app.include_router(profiles_router)
app.include_router(schedules_router)

# os.getenv (not Settings) because mount must happen at module level, before lifespan.
# Settings requires fellow_email/password which aren't available at import time in tests.
_mcp_enabled = os.getenv("FELLOW_MCP_ENABLED", "false").lower() == "true"

if _mcp_enabled:
    from fastmcp import FastMCP as _FastMCP

    from fellow_aiden_api.mcp_auth import McpApiKeyMiddleware

    _mcp_server = _FastMCP("fellow-aiden-coffee")
    _mcp_app = _mcp_server.http_app(path="/")
    _mcp_api_key = os.getenv("FELLOW_API_KEY")
    _mcp_app.add_middleware(McpApiKeyMiddleware, api_key=_mcp_api_key)
    app.mount("/mcp", _mcp_app)


@app.exception_handler(Exception)
async def catch_all_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
