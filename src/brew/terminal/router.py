"""WebSocket endpoint at /api/terminal/ws.

Thin: delegates to TerminalService.attached() and TerminalSession.run().
Auth via the existing `require_api_key` dependency (reads `X-API-Key` header
or `?api_key=` query param). Feature gate via `_require_terminal_enabled`
in `brew.main`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, WebSocket

from brew.terminal.dependencies import get_terminal_service

if TYPE_CHECKING:
    from brew.terminal.service import TerminalService

router = APIRouter()


@router.websocket("/terminal/ws")
async def terminal_ws(
    ws: WebSocket,
    service: Annotated[TerminalService, Depends(get_terminal_service)],
) -> None:
    await ws.accept()
    async with service.attached() as session:
        await session.run(ws)
