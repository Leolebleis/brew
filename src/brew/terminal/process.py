"""PTY-backed concrete TerminalProcessFacade implementation.

Forks tmux under a PTY. The tmux server outlives the WebSocket so the next
connection can reattach the same session — close() does NOT signal the child.
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import os
import pty
import struct
import termios

DEFAULT_WORKSPACE = "/app/brew-workspace"
DEFAULT_SESSION = "claude"

_NOT_STARTED = "start() must be called before {}()"


class TmuxPtyProcess:
    def __init__(
        self,
        *,
        workspace_dir: str = DEFAULT_WORKSPACE,
        session_name: str = DEFAULT_SESSION,
        argv: list[str] | None = None,
    ) -> None:
        self._argv = argv or [
            "tmux",
            "new-session",
            "-A",
            "-s",
            session_name,
            "-c",
            workspace_dir,
            "claude",
        ]
        self._fd: int | None = None
        self._pid: int | None = None

    async def start(self) -> None:
        pid, fd = pty.fork()
        if pid == 0:
            # tmux refuses to attach with TERM=dumb / unset ("open terminal
            # failed: terminal does not support clear"). xterm-256color is
            # what xterm.js emulates and ships in ncurses-base.
            os.environ["TERM"] = "xterm-256color"
            os.execvp(self._argv[0], self._argv)  # noqa: S606  PTY child exec
        self._pid = pid
        self._fd = fd

    async def read(self, n: int) -> bytes:
        if self._fd is None:
            return b""
        try:
            return await asyncio.to_thread(os.read, self._fd, n)
        except OSError:
            # PTY closed (child exited) — clean EOF.
            return b""

    async def write(self, data: bytes) -> None:
        if self._fd is None:
            raise RuntimeError(_NOT_STARTED.format("write"))
        os.write(self._fd, data)

    async def resize(self, rows: int, cols: int) -> None:
        if self._fd is None:
            raise RuntimeError(_NOT_STARTED.format("resize"))
        fcntl.ioctl(
            self._fd,
            termios.TIOCSWINSZ,
            struct.pack("HHHH", rows, cols, 0, 0),
        )

    async def close(self) -> None:
        if self._fd is not None:
            with contextlib.suppress(OSError):
                os.close(self._fd)
            self._fd = None
        # Deliberately do NOT kill self._pid: tmux server must outlive the
        # WebSocket so the next attach reuses the same session.
