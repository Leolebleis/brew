"""TmuxPtyProcess integration test against /bin/cat.

We don't test the real tmux+claude invocation here — that requires Anthropic
OAuth state and would burn tokens. Instead, exec `/bin/cat`, which echoes its
input back, and verify start/write/read/close round-trips.
"""

from __future__ import annotations

import asyncio

from brew.terminal.process import TmuxPtyProcess


async def _read_until(process: TmuxPtyProcess, expected: bytes, timeout: float = 2.0) -> bytes:  # noqa: ASYNC109  test helper, deadline-based polling
    accumulated = b""
    deadline = asyncio.get_running_loop().time() + timeout
    while expected not in accumulated:
        remaining = deadline - asyncio.get_running_loop().time()
        if remaining <= 0:
            msg = f"timed out; got {accumulated!r}, wanted {expected!r}"
            raise AssertionError(msg)
        chunk = await asyncio.wait_for(process.read(4096), timeout=remaining)
        if not chunk:
            msg = f"unexpected EOF; got {accumulated!r}"
            raise AssertionError(msg)
        accumulated += chunk
    return accumulated


async def test_round_trips_bytes_through_a_real_pty() -> None:
    process = TmuxPtyProcess(argv=["/bin/cat"])
    await process.start()
    try:
        await process.write(b"hello world\n")
        out = await _read_until(process, b"hello world")
        assert b"hello world" in out
    finally:
        await process.close()


async def test_close_releases_fd() -> None:
    process = TmuxPtyProcess(argv=["/bin/cat"])
    await process.start()
    await process.close()

    # After close, read returns EOF (b"") rather than blocking.
    out = await asyncio.wait_for(process.read(4096), timeout=1.0)
    assert out == b""


async def test_resize_does_not_raise_on_live_pty() -> None:
    process = TmuxPtyProcess(argv=["/bin/cat"])
    await process.start()
    try:
        await process.resize(24, 80)  # smoke: no exception
    finally:
        await process.close()
