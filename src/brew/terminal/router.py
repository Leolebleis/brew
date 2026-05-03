"""WebSocket endpoint at /api/terminal/ws."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, WebSocket, status

from brew.dependencies import get_settings
from brew.terminal.dependencies import get_terminal_service

if TYPE_CHECKING:
    from brew.config import Settings
    from brew.terminal.service import TerminalService

router = APIRouter()


def _extract_api_key(ws: WebSocket) -> str | None:
    return ws.headers.get("x-api-key") or ws.query_params.get("api_key")


@router.websocket("/terminal/ws")
async def terminal_ws(
    ws: WebSocket,
    service: Annotated[TerminalService, Depends(get_terminal_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    # Auth inline: include_router(dependencies=[...]) propagates deps to WS
    # routes, but FastAPI's WS dependency resolver doesn't inject Header/Query
    # parameters the same way HTTP does, so the shared `require_api_key` dep
    # can't read the credential. Read directly from the WS scope instead.
    if settings.api_key is not None:
        provided = _extract_api_key(ws)
        if provided is None or provided != settings.api_key.get_secret_value():
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await ws.accept()
    async with service.attached() as session:
        await session.run(ws)
