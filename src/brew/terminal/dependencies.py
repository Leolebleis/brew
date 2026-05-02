"""Dependency-injection wiring for the terminal context."""

from __future__ import annotations

from brew.terminal.process import TmuxPtyProcess
from brew.terminal.service import TerminalService


def get_terminal_service() -> TerminalService:
    return TerminalService(process_factory=TmuxPtyProcess)
