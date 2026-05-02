"""Domain-level Protocol for a terminal subprocess.

The facade is the contract `TerminalSession` depends on. The concrete
implementation (`TmuxPtyProcess` in `process.py`) lives in the infrastructure
layer; tests substitute an in-memory `FakeProcess` to exercise the service
without spawning a real PTY.
"""

from typing import Protocol


class TerminalProcessFacade(Protocol):
    """Bidirectional byte stream backed by a child process.

    Lifecycle: `start()` once, then arbitrarily many `read`/`write`/`resize`
    calls, then `close()` once. Implementations need not be thread-safe; the
    service uses a single async task per direction.
    """

    async def start(self) -> None: ...

    async def read(self, n: int) -> bytes:
        """Block until at least one byte is available; return up to `n` bytes.

        Returns an empty `bytes` object on clean EOF.
        """
        ...

    async def write(self, data: bytes) -> None: ...

    async def resize(self, rows: int, cols: int) -> None: ...

    async def close(self) -> None: ...
