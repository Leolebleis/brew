import json
from typing import Any

from fastmcp import FastMCP

from brew.bags.service import BagService
from brew.errors import DomainError, NotFoundError
from brew.journal.model.entry import TastingAxes
from brew.journal.palate import BeanDimensions, PalateQuery
from brew.journal.service import JournalService
from brew.mcp_utils import domain_error_to_resource_payload, domain_error_to_tool_error, jsonify


async def _resolve_log_tasting(  # noqa: PLR0913
    service: JournalService,
    bag_service: BagService,
    entry_id: str | None,
    bag_id: str | None,
    acidity: int | None,
    bitterness: int | None,
    body: int | None,
    sweetness: int | None,
    strength: int | None,
    flavor_tags: list[str] | None,
    note_text: str | None,
    rating: int | None,
) -> dict[str, Any]:
    """Core logic for log_tasting — extracted to keep register_journal_mcp under the complexity cap."""
    # Resolve bag
    bag = None
    if bag_id:
        bag = await bag_service.get(bag_id)
    else:
        bag = await bag_service.get_active()

    # Resolve target entry
    if entry_id:
        target = entry_id
    else:
        entries = await service.list(bag_id=bag.id if bag else None, limit=1)
        if not entries:
            resource_kind = "journal_entry"
            resource_id = bag.id if bag else "active-bag"
            raise NotFoundError.for_resource(resource_kind, resource_id)
        target = entries[0].id

    # Build bean dimensions snapshot from bag
    bean_dimensions_snapshot: dict[str, Any] | None = None
    if bag is not None:
        bean_dimensions_snapshot = {
            "varietal": getattr(bag, "varietal", None),
            "process": getattr(bag, "process", None),
            "roast_level": getattr(bag, "roast_level", None),
            "origin": getattr(bag, "origin", None),
            "altitude_masl": getattr(bag, "altitude_masl", None),
        }

    await service.record_tasting(
        target,
        axes=TastingAxes(
            acidity=acidity,
            bitterness=bitterness,
            body=body,
            sweetness=sweetness,
            strength=strength,
        ),
        flavor_tags=flavor_tags or [],
        note_text=note_text,
        rating=rating,
        bean_dimensions_snapshot=bean_dimensions_snapshot,
    )
    return {"status": "logged", "entry_id": target}


def register_journal_mcp(mcp: FastMCP, service: JournalService, bag_service: BagService, palate: PalateQuery) -> None:
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

    @mcp.tool(
        description=(
            "Log how a brew tasted: signed axes (-2..+2, 0=balanced), flavor tags, note, 1-5 rating. "
            "Omit entry_id to apply to the most recent brew of the active bag. "
            "Snapshots the bag's bean dimensions for palate learning."
        ),
    )
    async def log_tasting(  # noqa: PLR0913
        entry_id: str | None = None,
        bag_id: str | None = None,
        acidity: int | None = None,
        bitterness: int | None = None,
        body: int | None = None,
        sweetness: int | None = None,
        strength: int | None = None,
        flavor_tags: list[str] | None = None,
        note_text: str | None = None,
        rating: int | None = None,
    ) -> str:
        try:
            result = await _resolve_log_tasting(
                service,
                bag_service,
                entry_id,
                bag_id,
                acidity,
                bitterness,
                body,
                sweetness,
                strength,
                flavor_tags,
                note_text,
                rating,
            )
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return jsonify(result)

    @mcp.tool(
        description=(
            "Predict how the user will likely perceive a bean from their tasting history of similar beans "
            "(weighted nearest-neighbour). Returns mean axes, confidence (0-1), neighbour count, and "
            "contributing brews. Call when building a new profile to pre-correct toward the user's palate."
        ),
    )
    async def query_palate(  # noqa: PLR0913
        varietal: str | None = None,
        process: str | None = None,
        roast_level: str | None = None,
        origin: str | None = None,
        altitude_masl: int | None = None,
        flavor_tags: list[str] | None = None,
    ) -> str:
        try:
            tendency = await palate.tendency_for(
                BeanDimensions(
                    varietal=varietal,
                    process=process,
                    roast_level=roast_level,
                    origin=origin,
                    altitude_masl=altitude_masl,
                    flavor_tags=flavor_tags or [],
                )
            )
        except DomainError as e:
            raise domain_error_to_tool_error(e) from e
        return json.dumps(
            {
                "tendency": tendency.tendency,
                "confidence": tendency.confidence,
                "n": tendency.n,
                "neighbours": tendency.neighbours,
            }
        )
