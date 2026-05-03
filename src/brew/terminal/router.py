"""WebSocket endpoint at /api/terminal/ws.

Auth and feature-gating are enforced INLINE rather than via
include_router(dependencies=[...]) — FastAPI silently 403s WS upgrades
when deps are propagated through include_router, regardless of whether
the deps actually raise. See PR commit history for the investigation.
"""

from __future__ import annotations

import os

from fastapi import APIRouter, WebSocket, status

from brew.dependencies import get_settings
from brew.terminal.dependencies import get_terminal_service

router = APIRouter()


def _terminal_enabled() -> bool:
    chat = os.getenv("FELLOW_CHAT_ENABLED", "false").lower() == "true"
    mcp = os.getenv("FELLOW_MCP_ENABLED", "false").lower() == "true"
    return chat and mcp


def _extract_api_key(ws: WebSocket) -> str | None:
    return ws.headers.get("x-api-key") or ws.query_params.get("api_key")


def _api_key_valid(ws: WebSocket) -> bool:
    expected = get_settings().api_key
    if expected is None:
        return True
    provided = _extract_api_key(ws)
    return provided is not None and provided == expected.get_secret_value()


@router.websocket("/terminal/ws")
async def terminal_ws(ws: WebSocket) -> None:
    if not _terminal_enabled() or not _api_key_valid(ws):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    service = get_terminal_service()
    await ws.accept()
    async with service.attached() as session:
        await session.run(ws)
