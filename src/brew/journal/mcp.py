from fastmcp import FastMCP

from brew.errors import DomainError
from brew.journal.service import JournalService
from brew.mcp_utils import domain_error_to_resource_payload, jsonify


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
        try:
            entries = await service.list(limit=50)
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(entries)

    @mcp.resource(
        "coffee://journal/{entry_id}",
        description="A single journal entry by ID, including the profile snapshot frozen at brew time.",
    )
    async def get_entry(entry_id: str) -> str:
        try:
            entry = await service.get(entry_id)
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(entry)
