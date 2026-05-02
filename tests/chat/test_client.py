"""PydanticAiChatAgent — integration tests with pydantic-ai TestModel.

TestModel produces a deterministic event sequence; we assert the mapper
correctly translates it into AgentStreamEvents including the terminal AgentDone.
"""

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.anthropic import AnthropicProvider

from brew.chat.client import PydanticAiChatAgent
from brew.chat.model.event import AgentDone, TextDelta


@pytest.fixture
def chat_agent() -> PydanticAiChatAgent:
    """Build a PydanticAiChatAgent with a real pydantic-ai Agent that we'll override with TestModel."""
    model = AnthropicModel(
        "claude-sonnet-4-6",
        provider=AnthropicProvider(api_key="sk-ant-test"),
    )
    agent = Agent(model, instructions="test")
    return PydanticAiChatAgent(agent=agent)


async def test_stream_yields_text_delta_then_agent_done(chat_agent: PydanticAiChatAgent) -> None:
    test_model = TestModel(custom_output_text="Hello, world!")
    with chat_agent.inner.override(model=test_model):
        events = [ev async for ev in chat_agent.stream(prompt="hi", history=[])]

    # Must contain at least one TextDelta and exactly one terminal AgentDone.
    text_deltas = [e for e in events if isinstance(e, TextDelta)]
    agent_dones = [e for e in events if isinstance(e, AgentDone)]
    assert len(text_deltas) >= 1
    assert len(agent_dones) == 1
    # AgentDone payload is a dict (the ModelResponse JSON)
    assert isinstance(agent_dones[0].payload, dict)


async def test_stream_with_history_round_trips(chat_agent: PydanticAiChatAgent) -> None:
    """History payloads from a previous turn should deserialize and be passed through."""
    # Take a full turn first to capture an authentic ModelMessage payload.
    test_model = TestModel(custom_output_text="first")
    history_payload: dict | None = None
    with chat_agent.inner.override(model=test_model):
        async for ev in chat_agent.stream(prompt="first", history=[]):
            if isinstance(ev, AgentDone):
                history_payload = ev.payload

    assert history_payload is not None

    # Second turn: pass the history back. Should not error.
    test_model_2 = TestModel(custom_output_text="second")
    second_done = None
    with chat_agent.inner.override(model=test_model_2):
        async for ev in chat_agent.stream(prompt="second", history=[history_payload]):
            if isinstance(ev, AgentDone):
                second_done = ev

    assert second_done is not None


async def test_stream_with_empty_history(chat_agent: PydanticAiChatAgent) -> None:
    """history=[] is a valid first-turn shape."""
    test_model = TestModel(custom_output_text="hi")
    with chat_agent.inner.override(model=test_model):
        events = [ev async for ev in chat_agent.stream(prompt="hello", history=[])]
    assert any(isinstance(ev, AgentDone) for ev in events)
