"""Tests for build_chat_agent factory."""

from unittest.mock import AsyncMock

import pytest
from fastmcp import FastMCP
from pydantic_ai.models.test import TestModel

from brew.bags.service import BagService
from brew.chat.agent import build_chat_agent
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


def test_agent_builds_without_error(
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    agent = build_chat_agent(
        settings=settings,
        mcp_server=mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    assert agent is not None


def test_agent_registers_local_tools(
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    agent = build_chat_agent(
        settings=settings,
        mcp_server=mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    # _AgentFunctionToolset is always at index 0; its .tools dict is keyed by name
    function_toolset = agent.toolsets[0]
    tool_names = set(function_toolset.tools.keys())
    assert "query_journal" in tool_names
    assert "find_historical_bag" in tool_names


async def test_agent_uses_test_model_for_simple_query(
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> None:
    agent = build_chat_agent(
        settings=settings,
        mcp_server=mcp_server,
        journal_service=journal_service,
        bag_service=bag_service,
    )
    with agent.override(model=TestModel(call_tools=[])):
        result = await agent.run("hello")
    assert result.output
