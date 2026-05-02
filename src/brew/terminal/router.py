"""WebSocket endpoint at /api/terminal/ws."""

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
