import json
from unittest.mock import AsyncMock

from fastmcp import FastMCP

from brew.journal.mcp import register_journal_mcp
from brew.journal.palate import PalateTendency


async def test_query_palate_returns_tendency() -> None:
    journal_service = AsyncMock()
    bag_service = AsyncMock()
    palate = AsyncMock()
    palate.tendency_for.return_value = PalateTendency(
        tendency={"acidity": 1.5},
        confidence=0.6,
        n=3,
        neighbours=[{"entry_id": "e1", "similarity": 0.9, "axes": {}, "rating": 3}],
    )
    mcp = FastMCP("test")
    register_journal_mcp(mcp, journal_service, bag_service, palate)

    result = await mcp.call_tool("query_palate", {"varietal": "Geisha", "process": "natural"})
    payload = json.loads(result.content[0].text)
    assert payload["confidence"] == 0.6
    assert payload["tendency"]["acidity"] == 1.5


async def test_log_tasting_snapshots_active_bag_dimensions() -> None:
    journal_service = AsyncMock()
    bag_service = AsyncMock()
    bag = AsyncMock()
    bag.id = "bag-1"
    bag.varietal, bag.process, bag.roast_level, bag.origin, bag.altitude_masl = (
        "Geisha",
        "natural",
        "light",
        "Huila",
        1650,
    )
    bag_service.get_active.return_value = bag
    latest = AsyncMock()
    latest.id = "entry-9"
    journal_service.list.return_value = [latest]

    mcp = FastMCP("test")
    register_journal_mcp(mcp, journal_service, bag_service, AsyncMock())

    await mcp.call_tool(
        "log_tasting",
        {
            "acidity": 2,
            "flavor_tags": ["floral"],
            "note_text": "sharp",
            "rating": 3,
        },
    )
    journal_service.record_tasting.assert_awaited_once()
    kwargs = journal_service.record_tasting.call_args.kwargs
    assert kwargs["bean_dimensions_snapshot"]["varietal"] == "Geisha"
    assert kwargs["flavor_tags"] == ["floral"]
