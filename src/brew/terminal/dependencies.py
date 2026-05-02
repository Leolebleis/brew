"""Dependency-injection wiring for the terminal context."""

from __future__ import annotations

from brew.terminal.process import TmuxPtyProcess
from brew.terminal.service import TerminalService


def get_terminal_service() -> TerminalService:
    """Default factory: TmuxPtyProcess with workspace defaults.

    Tests override via `app.dependency_overrides[get_terminal_service]`.
    """
    return TerminalService(process_factory=TmuxPtyProcess)
