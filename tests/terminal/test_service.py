"""TerminalSession.run unit tests against an in-memory FakeProcess.

The fake replaces `pty.fork()` + `os.read/write` with asyncio.Queues so we can
drive the bidirectional pump deterministically. Real PTY plumbing is covered
in tests/terminal/test_process.py.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock

from fastapi import WebSocketDisconnect

from brew.terminal.facade import TerminalProcessFacade
from brew.terminal.service import TerminalService, TerminalSession


class FakeProcess(TerminalProcessFacade):
    """In-memory facade. Exposes inbound/outbound queues for the test to drive."""

    def __init__(self) -> None:
        self.outbound: asyncio.Queue[bytes] = asyncio.Queue()  # process → ws
        self.inbound: list[bytes] = []  # ws → process
        self.resizes: list[tuple[int, int]] = []
        self.started = False
        self.closed = False

    async def start(self) -> None:
        self.started = True

    async def read(self, n: int) -> bytes:  # noqa: ARG002 — n unused in fake
        return await self.outbound.get()

    async def write(self, data: bytes) -> None:
        self.inbound.append(data)

    async def resize(self, rows: int, cols: int) -> None:
        self.resizes.append((rows, cols))

    async def close(self) -> None:
        self.closed = True


def _make_ws(messages: list[dict[str, Any]]) -> AsyncMock:
    """Build a mock WebSocket that yields the given receive messages then raises
    WebSocketDisconnect, matching FastAPI's behavior on client close."""
    ws = AsyncMock()
    queue = list(messages)

    async def receive() -> dict[str, Any]:
        if not queue:
            raise WebSocketDisconnect(code=1000)
        return queue.pop(0)

    ws.receive.side_effect = receive
    ws.send_bytes = AsyncMock()
    return ws


async def test_run_pumps_process_output_to_ws_send_bytes() -> None:
    process = FakeProcess()
    session = TerminalSession(process)
    ws = _make_ws([])  # no inbound messages → immediate disconnect

    # Seed an outbound chunk before the pump starts; the read() task will
    # pick it up and forward to ws.send_bytes.
    await process.outbound.put(b"hello")

    await session.run(ws)

    ws.send_bytes.assert_any_await(b"hello")


async def test_run_forwards_ws_bytes_to_process_write() -> None:
    process = FakeProcess()
    session = TerminalSession(process)
    ws = _make_ws([{"type": "websocket.receive", "bytes": b"abc"}])

    await session.run(ws)

    assert b"abc" in process.inbound


async def test_run_handles_resize_text_frame() -> None:
    process = FakeProcess()
    session = TerminalSession(process)
    resize_json = json.dumps({"type": "resize", "rows": 24, "cols": 80})
    ws = _make_ws([{"type": "websocket.receive", "text": resize_json}])

    await session.run(ws)

    assert process.resizes == [(24, 80)]


async def test_run_returns_cleanly_on_websocket_disconnect() -> None:
    process = FakeProcess()
    session = TerminalSession(process)
    ws = _make_ws([])

    # Should not raise.
    await session.run(ws)


async def test_service_attached_starts_and_closes_process() -> None:
    process = FakeProcess()
    service = TerminalService(process_factory=lambda: process)

    async with service.attached() as session:
        assert isinstance(session, TerminalSession)
        assert process.started
        assert not process.closed

    assert process.closed
