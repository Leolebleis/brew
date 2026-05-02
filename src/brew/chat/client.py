"""Chat agent — Protocol + pydantic-ai concrete impl."""

from collections.abc import AsyncIterator
from typing import Any, Protocol

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessagesTypeAdapter

from brew.chat.mapper import pydantic_ai_to_agent_event
from brew.chat.model.event import AgentStreamEvent


class ChatAgent(Protocol):
    def stream(
        self,
        prompt: str,
        history: list[dict[str, Any]],
    ) -> AsyncIterator[AgentStreamEvent]: ...


class PydanticAiChatAgent:
    """Concrete `ChatAgent` impl wrapping a pydantic-ai `Agent`."""

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    @property
    def inner(self) -> Agent:
        """Underlying pydantic-ai Agent — for tests + TestModel overrides only."""
        return self._agent

    async def stream(
        self,
        prompt: str,
        history: list[dict[str, Any]],
    ) -> AsyncIterator[AgentStreamEvent]:
        message_history = ModelMessagesTypeAdapter.validate_python(history)

        async for event in self._agent.run_stream_events(prompt, message_history=message_history):
            mapped = pydantic_ai_to_agent_event(event)
            if mapped is not None:
                yield mapped
