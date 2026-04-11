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


def _create_fellow(email: str, password: str) -> FellowAiden:
    return FellowAiden(email, password)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = Settings()

    fellow = await asyncio.to_thread(_create_fellow, settings.fellow_email, settings.fellow_password.get_secret_value())

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
async def catch_all_handler(_request: Request, _exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
