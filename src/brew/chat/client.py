"""Chat agent — Protocol + pydantic-ai concrete impl.

`ChatAgent` is the seam between `ChatService` and pydantic-ai. The service
yields `ChatStreamEvent`s on the wire; the Protocol yields `AgentStreamEvent`s
(includes `AgentDone(payload)` for the service to persist before emitting
`Done(message_id)` to the wire).
"""

from collections.abc import AsyncIterator
from typing import Any, Protocol

from pydantic_ai import Agent

from brew.chat.model.event import AgentStreamEvent


class ChatAgent(Protocol):
    def stream(
        self,
        prompt: str,
        history: list[dict[str, Any]],
    ) -> AsyncIterator[AgentStreamEvent]: ...


class PydanticAiChatAgent:
    """Concrete `ChatAgent` impl wrapping a pydantic-ai `Agent`.

    Implementation lands in Task 7. Public attribute `inner` exposes the
    underlying pydantic-ai Agent for tests + lifespan model overrides.
    """

    def __init__(self, agent: Agent) -> None:
        self._agent = agent

    @property
    def inner(self) -> Agent:
        """Underlying pydantic-ai Agent — for tests + TestModel overrides only."""
        return self._agent

    async def stream(
        self,
        prompt: str,  # noqa: ARG002
        history: list[dict[str, Any]],  # noqa: ARG002
    ) -> AsyncIterator[AgentStreamEvent]:
        msg = "PydanticAiChatAgent.stream not yet implemented (Task 7)"
        raise NotImplementedError(msg)
        yield  # pragma: no cover — makes mypy/ty happy: function is async generator
