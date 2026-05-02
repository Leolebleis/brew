import asyncio
import logging
import os
import pathlib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

import aiosqlite
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from brew.aiden.dependencies import build_fellow_client, get_aiden_settings
from brew.aiden.device.client import FellowDeviceHttpClient
from brew.aiden.device.dependencies import get_device_service
from brew.aiden.device.router import router as device_router
from brew.aiden.device.service import DeviceService
from brew.aiden.profiles.client import FellowProfileHttpClient
from brew.aiden.profiles.dependencies import get_profile_service
from brew.aiden.profiles.router import router as profiles_router
from brew.aiden.profiles.service import ProfileService
from brew.aiden.schedules.brew_now import BrewNowService
from brew.aiden.schedules.client import FellowScheduleHttpClient
from brew.aiden.schedules.dependencies import get_brew_now_service, get_schedule_service
from brew.aiden.schedules.router import router as schedules_router
from brew.aiden.schedules.service import ScheduleService
from brew.bags.dependencies import get_bag_service
from brew.bags.repository import BagSqliteRepository
from brew.bags.router import router as bags_router
from brew.bags.schema import BAGS_SCHEMA
from brew.bags.service import BagService
from brew.chat.router import router as chat_router
from brew.chat.schema import CHAT_SCHEMA
from brew.db import init_db, open_db
from brew.dependencies import get_settings, require_api_key
from brew.events.broadcaster import EventBroadcaster
from brew.events.bus import EventBus
from brew.events.dependencies import get_event_broadcaster
from brew.events.domain import (
    BagActivated,
    BagFinished,
    BrewCompleted,
    JournalEntryCreated,
    WaterRefilled,
)
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


_BROADCAST_EVENTS = (
    JournalEntryCreated,
    BrewCompleted,
    BagActivated,
    BagFinished,
    WaterRefilled,
)


def _wire_event_subscribers(
    bus: EventBus,
    broadcaster: EventBroadcaster,
    journal_service: JournalService,
    bag_service: BagService,
    water_service: WaterService,
) -> None:
    for event in _BROADCAST_EVENTS:
        bus.subscribe(event, broadcaster.broadcast)
    bus.subscribe(BrewCompleted, make_journal_auto_log_handler(journal_service, bag_service))
    bus.subscribe(JournalEntryCreated, make_water_decrement_handler(water_service))
    bus.subscribe(JournalEntryCreated, make_bag_decrement_handler(bag_service))


def _register_aiden_mcp(
    device_service: DeviceService,
    profile_service: ProfileService,
    schedule_service: ScheduleService,
    brew_now_service: BrewNowService,
) -> None:
    from brew.aiden.device.mcp import register_device_mcp  # noqa: PLC0415
    from brew.aiden.profiles.mcp import register_profile_mcp  # noqa: PLC0415
    from brew.aiden.schedules.mcp import register_brew_now_mcp, register_schedule_mcp  # noqa: PLC0415

    register_device_mcp(_mcp_server, device_service)
    register_profile_mcp(_mcp_server, profile_service)
    register_schedule_mcp(_mcp_server, schedule_service)
    register_brew_now_mcp(_mcp_server, brew_now_service)


def _register_domain_mcp(
    water_service: WaterService,
    bag_service: BagService,
    journal_service: JournalService,
) -> None:
    from brew.bags.mcp import register_bags_mcp  # noqa: PLC0415
    from brew.journal.mcp import register_journal_mcp  # noqa: PLC0415
    from brew.water.mcp import register_water_mcp  # noqa: PLC0415

    register_water_mcp(_mcp_server, water_service)
    register_bags_mcp(_mcp_server, bag_service)
    register_journal_mcp(_mcp_server, journal_service)


async def _wire_chat(
    app: FastAPI,
    db_conn: aiosqlite.Connection,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    from brew.chat.agent import build_chat_agent  # noqa: PLC0415
    from brew.chat.config import get_chat_settings  # noqa: PLC0415
    from brew.chat.dependencies import get_chat_service  # noqa: PLC0415
    from brew.chat.repository import ChatSqliteRepository  # noqa: PLC0415
    from brew.chat.service import ChatService  # noqa: PLC0415

    chat_settings = get_chat_settings()
    chat_agent = build_chat_agent(
        settings=chat_settings,
        mcp_server=_mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    chat_service = ChatService(repo=ChatSqliteRepository(conn=db_conn), agent=chat_agent)
    app.dependency_overrides[get_chat_service] = lambda: chat_service


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
    brew_now_service = BrewNowService(
        schedule_service=schedule_service,
        profile_service=profile_service,
        device_service=device_service,
    )

    db_conn = await open_db(settings.database_path)
    await init_db(db_conn, [WATER_SCHEMA, BAGS_SCHEMA, JOURNAL_SCHEMA, CHAT_SCHEMA])

    bus = EventBus()
    broadcaster = EventBroadcaster()
    water_service = WaterService(repo=WaterSqliteRepository(conn=db_conn), bus=bus)
    bag_service = BagService(repo=BagSqliteRepository(conn=db_conn), bus=bus)
    journal_service = JournalService(repo=JournalSqliteRepository(conn=db_conn), bus=bus)
    _wire_event_subscribers(bus, broadcaster, journal_service, bag_service, water_service)

    poller_interval = float(os.getenv("FELLOW_POLLER_INTERVAL_SECONDS", "5.0"))
    poller = DeviceBrewingPoller(device_service=device_service, bus=bus, interval_seconds=poller_interval)
    poller_task = asyncio.create_task(poller.run(), name="device-brewing-poller")

    app.dependency_overrides.update(
        {
            get_device_service: lambda: device_service,
            get_profile_service: lambda: profile_service,
            get_schedule_service: lambda: schedule_service,
            get_brew_now_service: lambda: brew_now_service,
            get_water_service: lambda: water_service,
            get_bag_service: lambda: bag_service,
            get_journal_service: lambda: journal_service,
            get_event_broadcaster: lambda: broadcaster,
        }
    )

    if _mcp_enabled:
        _register_aiden_mcp(device_service, profile_service, schedule_service, brew_now_service)
        _register_domain_mcp(water_service, bag_service, journal_service)

    if _chat_enabled and _mcp_enabled:
        await _wire_chat(app, db_conn, journal_service, bag_service)

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
app.include_router(device_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(profiles_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(schedules_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(water_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(bags_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(journal_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(events_router, prefix="/api", dependencies=[Depends(require_api_key)])
app.include_router(chat_router, prefix="/api", dependencies=[Depends(require_api_key)])

# os.getenv (not Settings) because mount must happen at module level, before lifespan.
# Settings requires fellow_email/password which aren't available at import time in tests.
_mcp_enabled = os.getenv("FELLOW_MCP_ENABLED", "false").lower() == "true"
_chat_enabled = os.getenv("FELLOW_CHAT_ENABLED", "false").lower() == "true"

if _mcp_enabled:
    from fastmcp import FastMCP as _FastMCP

    from brew.mcp_auth import McpApiKeyMiddleware

    _mcp_server = _FastMCP("fellow-aiden-coffee")
    _mcp_app = _mcp_server.http_app(path="/")
    _mcp_api_key = os.getenv("FELLOW_API_KEY")
    _mcp_app.add_middleware(McpApiKeyMiddleware, api_key=_mcp_api_key)
    app.mount("/mcp", _mcp_app)

# Frontend SPA mount — must come AFTER all routers/mounts so `/health`, `/api/*`,
# and `/mcp` take precedence. `html=True` falls back to index.html for unknown
# paths (SPA client-side routing). Gated on dist/ existing so tests don't need
# a built frontend.
#
# BREW_FRONTEND_DIST overrides the relative path heuristic. Required in Docker
# (`--no-editable` install puts brew/main.py inside .venv site-packages, so the
# parent.parent.parent walk doesn't reach /app/frontend/dist). Local dev leaves
# it unset and relies on the source-tree-relative path.
_FRONTEND_DIST_ENV = os.environ.get("BREW_FRONTEND_DIST")
_FRONTEND_DIST = (
    pathlib.Path(_FRONTEND_DIST_ENV)
    if _FRONTEND_DIST_ENV
    else pathlib.Path(__file__).parent.parent.parent / "frontend" / "dist"
)
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")


@app.exception_handler(Exception)
async def catch_all_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "unknown", "message": "Internal server error", "context": {}}},
    )
