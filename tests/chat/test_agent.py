"""Tests for build_chat_agent factory."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from pydantic_ai.models.test import TestModel

from brew.bags.service import BagService
from brew.chat.agent import build_chat_agent
from brew.chat.client import PydanticAiChatAgent
from brew.chat.config import ChatSettings
from brew.journal.service import JournalService


@pytest.fixture
def settings() -> ChatSettings:
    return ChatSettings(  # ty: ignore[missing-argument]
        anthropic_api_key="sk-ant-test",
        model="claude-sonnet-4-6",
        chat_enabled=True,
    )


@pytest.fixture
def mcp_server() -> FastMCP:
    return FastMCP("test-mcp")


@pytest.fixture
def journal_service() -> JournalService:
    return AsyncMock(spec=JournalService)


@pytest.fixture
def bag_service() -> BagService:
    return AsyncMock(spec=BagService)


def test_returns_pydantic_ai_chat_agent(
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    chat_agent = build_chat_agent(
        settings=settings,
        mcp_server=mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    assert isinstance(chat_agent, PydanticAiChatAgent)


def test_caches_both_instructions_and_tool_definitions(
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    chat_agent = build_chat_agent(
        settings=settings,
        mcp_server=mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    model_settings = chat_agent.inner.model_settings
    assert model_settings is not None
    assert model_settings.get("anthropic_cache_instructions") == "1h"
    assert model_settings.get("anthropic_cache_tool_definitions") == "1h"


async def test_runs_with_test_model_override(
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    chat_agent = build_chat_agent(
        settings=settings,
        mcp_server=mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    with chat_agent.inner.override(model=TestModel(custom_output_text="hi")):
        result = await chat_agent.inner.run("hello")
    assert result.output
