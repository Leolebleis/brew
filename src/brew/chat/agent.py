"""pydantic-ai Agent factory.

In-process FastMCPToolset registration avoids a localhost HTTP roundtrip
per tool call. The agent is built once per app lifespan; the toolset is
bound to brew's FastMCP instance at construction time.
"""

from fastmcp import FastMCP
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

from brew.bags.service import BagService
from brew.chat.client import PydanticAiChatAgent
from brew.chat.config import ChatSettings
from brew.chat.tools import make_find_historical_bag, make_query_journal
from brew.journal.service import JournalService

_INSTRUCTIONS = """\
You are the chat assistant for a personal Fellow Aiden coffee setup.
You can read live state via MCP resources, perform actions via MCP tools,
and look up past brew journal entries via your local tools. When the user
mentions a bean by name, check find_historical_bag before suggesting a
fresh recipe — they may have had it before.
"""


def build_chat_agent(
    *,
    settings: ChatSettings,
    mcp_server: FastMCP,
    journal_service: JournalService,
    bag_service: BagService,
) -> PydanticAiChatAgent:
    model = AnthropicModel(
        settings.model,
        provider=AnthropicProvider(api_key=settings.anthropic_api_key.get_secret_value()),
    )
    agent = Agent(
        model,
        instructions=_INSTRUCTIONS,
        toolsets=[FastMCPToolset(mcp_server)],
        tools=[
            make_query_journal(journal_service),
            make_find_historical_bag(bag_service),
        ],
        model_settings=AnthropicModelSettings(
            anthropic_cache_instructions="1h",
            anthropic_cache_tool_definitions="1h",
        ),
    )
    return PydanticAiChatAgent(agent=agent)
