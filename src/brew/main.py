import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

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
from brew.bags.dependencies import get_bag_service
from brew.bags.repository import BagSqliteRepository
from brew.bags.router import router as bags_router
from brew.bags.schema import BAGS_SCHEMA
from brew.bags.service import BagService
from brew.db import init_db, open_db
from brew.dependencies import get_settings, require_api_key
from brew.events.broadcaster import EventBroadcaster
from brew.events.bus import EventBus
from brew.events.dependencies import get_event_broadcaster
from brew.events.domain import BrewCompleted, JournalEntryCreated
from brew.events.poller import DeviceBrewingPoller
from brew.events.router import router as events_router
from brew.events.subscribers.bag_decrement import make_bag_decrement_handler
from brew.events.subscribers.journal_auto_log import make_journal_auto_log_handler
from brew.events.subscribers.water_decrement import make_water_decrement_handler
from brew.exception_handlers import register_exception_handlers
from brew.health.router import router as health_router
from brew.journal.dependencies import get_journal_service
from brew.journal.repository import JournalSqliteRepository
from brew.journal.router import router as journal_router
from brew.journal.schema import JOURNAL_SCHEMA
from brew.journal.service import JournalService
from brew.water.dependencies import get_water_service
from brew.water.repository import WaterSqliteRepository
from brew.water.router import router as water_router
from brew.water.schema import WATER_SCHEMA
from brew.water.service import WaterService

logger = logging.getLogger(__name__)


def _wire_event_subscribers(
    bus: EventBus,
    broadcaster: EventBroadcaster,
    journal_service: JournalService,
    bag_service: BagService,
    water_service: WaterService,
) -> None:
    bus.subscribe(JournalEntryCreated, broadcaster.broadcast)
    bus.subscribe(BrewCompleted, make_journal_auto_log_handler(journal_service, bag_service))
    bus.subscribe(JournalEntryCreated, make_water_decrement_handler(water_service))
    bus.subscribe(JournalEntryCreated, make_bag_decrement_handler(bag_service))


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
    await init_db(db_conn, [WATER_SCHEMA, BAGS_SCHEMA, JOURNAL_SCHEMA])
    water_service = WaterService(repo=WaterSqliteRepository(conn=db_conn))
    bag_service = BagService(repo=BagSqliteRepository(conn=db_conn))

    bus = EventBus()
    broadcaster = EventBroadcaster()
    journal_service = JournalService(repo=JournalSqliteRepository(conn=db_conn), bus=bus)
    _wire_event_subscribers(bus, broadcaster, journal_service, bag_service, water_service)

    poller_interval = float(os.getenv("FELLOW_POLLER_INTERVAL_SECONDS", "5.0"))
    poller = DeviceBrewingPoller(device_service=device_service, bus=bus, interval_seconds=poller_interval)
    poller_task = asyncio.create_task(poller.run(), name="device-brewing-poller")

    app.dependency_overrides[get_device_service] = lambda: device_service
    app.dependency_overrides[get_profile_service] = lambda: profile_service
    app.dependency_overrides[get_schedule_service] = lambda: schedule_service
    app.dependency_overrides[get_water_service] = lambda: water_service
    app.dependency_overrides[get_bag_service] = lambda: bag_service
    app.dependency_overrides[get_journal_service] = lambda: journal_service
    app.dependency_overrides[get_event_broadcaster] = lambda: broadcaster

    if _mcp_enabled:
        from brew.aiden.device.mcp import register_device_mcp  # noqa: PLC0415
        from brew.aiden.profiles.mcp import register_profile_mcp  # noqa: PLC0415
        from brew.aiden.schedules.mcp import register_schedule_mcp  # noqa: PLC0415
        from brew.bags.mcp import register_bags_mcp  # noqa: PLC0415
        from brew.journal.mcp import register_journal_mcp  # noqa: PLC0415
        from brew.water.mcp import register_water_mcp  # noqa: PLC0415

        register_device_mcp(_mcp_server, device_service)
        register_profile_mcp(_mcp_server, profile_service)
        register_schedule_mcp(_mcp_server, schedule_service)
        register_water_mcp(_mcp_server, water_service)
        register_bags_mcp(_mcp_server, bag_service)
        register_journal_mcp(_mcp_server, journal_service)

    try:
        yield
    finally:
        poller_task.cancel()
        with suppress(asyncio.CancelledError):
            await poller_task
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
app.include_router(bags_router, dependencies=[Depends(require_api_key)])
app.include_router(journal_router, dependencies=[Depends(require_api_key)])
app.include_router(events_router, dependencies=[Depends(require_api_key)])

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
