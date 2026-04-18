import json
from dataclasses import asdict

from fastmcp import FastMCP

from brew.water.service import WaterService


def register_water_mcp(mcp: FastMCP, service: WaterService) -> None:
    @mcp.resource(
        "coffee://water",
        description="Estimated water remaining in the 1500 mL jug and last-refill timestamp.",
    )
    async def get_water() -> str:
        water = await service.get_water()
        return json.dumps(asdict(water), default=str)
