import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from brew.aiden.dependencies import build_fellow_client, get_aiden_settings
from brew.aiden.device.client import FellowDeviceHttpClient
from brew.aiden.device.dependencies import get_device_service
from brew.aiden.device.router import router as device_router
from brew.aiden.device.service import DeviceService
from brew.aiden.profiles.client import FellowProfileHttpClient
from brew.aiden.profiles.dependencies import get_profile_service
from brew.aiden.profiles.router import router as profiles_router
from brew.aiden.profiles.service import ProfileService
from brew.aiden.schedules.client import FellowScheduleHttpClient
from brew.aiden.schedules.dependencies import get_schedule_service
from brew.aiden.schedules.router import router as schedules_router
from brew.aiden.schedules.service import ScheduleService
from brew.db import init_db, open_db
from brew.dependencies import get_settings, require_api_key
from brew.exception_handlers import register_exception_handlers
from brew.health.router import router as health_router
from brew.water.dependencies import get_water_service
from brew.water.repository import WaterSqliteRepository
from brew.water.router import router as water_router
from brew.water.schema import WATER_SCHEMA
from brew.water.service import WaterService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _app_lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    _ = get_aiden_settings()  # validate aiden settings (raises if creds missing)
    fellow = await asyncio.to_thread(build_fellow_client)

    device_client = FellowDeviceHttpClient(fellow=fellow)
    profile_client = FellowProfileHttpClient(fellow=fellow)
    schedule_client = FellowScheduleHttpClient(fellow=fellow)

    device_service = DeviceService(client=device_client)
    profile_service = ProfileService(client=profile_client)
    schedule_service = ScheduleService(client=schedule_client)

    db_conn = await open_db(settings.database_path)
    await init_db(db_conn, [WATER_SCHEMA])
    water_service = WaterService(repo=WaterSqliteRepository(conn=db_conn))

    app.dependency_overrides[get_device_service] = lambda: device_service
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_schedule_service] = lambda: schedule_service
    app.dependency_overrides[get_water_service] = lambda: water_service

    if _mcp_enabled:
        from brew.aiden.device.mcp import register_device_mcp  # noqa: PLC0415
        from brew.aiden.profiles.mcp import register_profile_mcp  # noqa: PLC0415
        from brew.aiden.schedules.mcp import register_schedule_mcp  # noqa: PLC0415
        from brew.water.mcp import register_water_mcp  # noqa: PLC0415

        register_device_mcp(_mcp_server, device_service)
        register_profile_mcp(_mcp_server, profile_service)
        register_schedule_mcp(_mcp_server, schedule_service)
        register_water_mcp(_mcp_server, water_service)

    try:
        yield
    finally:
        await db_conn.close()
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
)

register_exception_handlers(app)

# /health is infrastructure-facing (Docker HEALTHCHECK, K8s probes) and must
# be reachable without auth — otherwise auth misconfig is indistinguishable
# from a dead app. Domain routers apply the guard individually.
app.include_router(health_router)
app.include_router(device_router, dependencies=[Depends(require_api_key)])
app.include_router(profiles_router, dependencies=[Depends(require_api_key)])
app.include_router(schedules_router, dependencies=[Depends(require_api_key)])
app.include_router(water_router, dependencies=[Depends(require_api_key)])

# os.getenv (not Settings) because mount must happen at module level, before lifespan.
# Settings requires fellow_email/password which aren't available at import time in tests.
_mcp_enabled = os.getenv("FELLOW_MCP_ENABLED", "false").lower() == "true"

if _mcp_enabled:
    from fastmcp import FastMCP as _FastMCP

    from brew.mcp_auth import McpApiKeyMiddleware

    _mcp_server = _FastMCP("fellow-aiden-coffee")
    _mcp_app = _mcp_server.http_app(path="/")
    _mcp_api_key = os.getenv("FELLOW_API_KEY")
    _mcp_app.add_middleware(McpApiKeyMiddleware, api_key=_mcp_api_key)
    app.mount("/mcp", _mcp_app)


@app.exception_handler(Exception)
async def catch_all_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "unknown", "message": "Internal server error", "context": {}}},
    )
