"""Chat API request/response models — wire shapes for the router."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatPostRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)


class ChatMessageResponse(BaseModel):
    id: str
    kind: Literal["request", "response"]
    payload: dict[str, Any]
    projected: dict[str, Any] | None
    created_at: datetime


class ChatGetResponse(BaseModel):
    messages: list[ChatMessageResponse]
    next_before_id: str | None
