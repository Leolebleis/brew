"""PTY-backed concrete TerminalProcessFacade implementation.

Forks a child process under a pseudoterminal, exec'ing `tmux new-session -A`
to attach-or-create the persistent claude session inside the configured
workspace directory. The tmux server outlives the WebSocket — disconnect
cancels reads but does NOT SIGHUP the server, so the next connection can
reattach the same session.
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

_NOT_STARTED_WRITE = "start() must be called before write()"
_NOT_STARTED_RESIZE = "start() must be called before resize()"


class TmuxPtyProcess:
    def __init__(
        self,
        *,
        workspace_dir: str = DEFAULT_WORKSPACE,
        session_name: str = DEFAULT_SESSION,
        argv: list[str] | None = None,
    ) -> None:
        """Construct a TmuxPtyProcess.

        `argv` is the exec target — defaults to the tmux attach-or-create
        invocation. Tests override it to spawn `/bin/cat` directly without
        tmux/claude.
        """
        self._workspace = workspace_dir
        self._session = session_name
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
            os.execvp(self._argv[0], self._argv)  # noqa: S606  PTY child exec
        self._pid = pid
        self._fd = fd

    async def read(self, n: int) -> bytes:
        if self._fd is None:
            # Not started, or already closed — clean EOF.
            return b""
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(None, os.read, self._fd, n)
        except OSError:
            # PTY closed (child exited) — treat as clean EOF.
            return b""

    async def write(self, data: bytes) -> None:
        if self._fd is None:
            raise RuntimeError(_NOT_STARTED_WRITE)
        os.write(self._fd, data)

    async def resize(self, rows: int, cols: int) -> None:
        if self._fd is None:
            raise RuntimeError(_NOT_STARTED_RESIZE)
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
        # Deliberately do NOT kill self._pid: when running tmux, the server
        # outlives this connection so the next WS attach finds the session
        # alive. For test usage with /bin/cat, the child exits when the fd
        # is closed.
