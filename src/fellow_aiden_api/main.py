import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from fellow_aiden_api.dependencies import require_api_key
from fellow_aiden_api.device.router import router as device_router
from fellow_aiden_api.health.router import router as health_router
from fellow_aiden_api.profiles.router import router as profiles_router
from fellow_aiden_api.schedules.router import router as schedules_router

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Fellow Aiden API",
    root_path="/coffee/api",
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
