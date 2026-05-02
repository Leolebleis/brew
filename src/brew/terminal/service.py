"""Terminal session orchestration."""

from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import WebSocket, WebSocketDisconnect

from brew.terminal.model import ResizeFrame

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from brew.terminal.facade import TerminalProcessFacade


class TerminalSession:
    """Bidirectional pump between a FastAPI WebSocket and a TerminalProcessFacade."""

    def __init__(self, process: TerminalProcessFacade) -> None:
        self._process = process

    async def run(self, ws: WebSocket) -> None:
        async def pump_to_ws() -> None:
            while True:
                data = await self._process.read(4096)
                if not data:
                    return
                await ws.send_bytes(data)

        task = asyncio.create_task(pump_to_ws())
        # Yield so pump_to_ws is scheduled before we receive — AsyncMocks in
        # tests resolve synchronously and would otherwise let an immediate
        # disconnect cancel the pump before any buffered output flushes.
        await asyncio.sleep(0)
        try:
            while True:
                msg = await ws.receive()
                if "bytes" in msg:
                    await self._process.write(msg["bytes"])
                elif "text" in msg:
                    frame = ResizeFrame.model_validate_json(msg["text"])
                    await self._process.resize(frame.rows, frame.cols)
        except WebSocketDisconnect:
            pass
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task


class TerminalService:
    """Factory + lifecycle manager for TerminalSession."""

    def __init__(self, *, process_factory: Callable[[], TerminalProcessFacade]) -> None:
        self._make_process = process_factory

    @asynccontextmanager
    async def attached(self) -> AsyncIterator[TerminalSession]:
        process = self._make_process()
        await process.start()
        try:
            yield TerminalSession(process)
        finally:
            await process.close()
