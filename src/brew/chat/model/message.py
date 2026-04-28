"""ChatMessage domain entities.

We persist pydantic-ai's `ModelMessage` JSON payloads (request OR response per
row), preserving full fidelity. ModelMessage is the canonical type pydantic-ai
uses for replay. Storing raw lets us re-run threads later without lossy
normalization.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

ChatMessageKind = Literal["request", "response"]


@dataclass(frozen=True)
class ChatMessage:
    id: str
    thread_id: str
    kind: ChatMessageKind
    payload: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True)
class ChatMessageCreate:
    thread_id: str
    kind: ChatMessageKind
    payload: dict[str, Any]
