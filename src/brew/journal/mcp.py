import json
from dataclasses import asdict

from fastmcp import FastMCP

from brew.journal.service import JournalService


def register_journal_mcp(mcp: FastMCP, service: JournalService) -> None:
    @mcp.resource(
        "coffee://journal",
        description=(
            "Recent brew journal entries, newest first (capped at 50). "
            "For filtered queries (by bag, profile, rating, date range), the chat backend "
            "exposes a `query_journal` tool."
        ),
    )
    async def list_entries() -> str:
        entries = await service.list(limit=50)
        return json.dumps([asdict(e) for e in entries], default=str)

    @mcp.resource(
        "coffee://journal/{entry_id}",
        description="A single journal entry by ID, including the profile snapshot frozen at brew time.",
    )
    async def get_entry(entry_id: str) -> str:
        entry = await service.get(entry_id)
        return json.dumps(asdict(entry), default=str)
