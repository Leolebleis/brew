from fastmcp import FastMCP

from brew.errors import DomainError
from brew.mcp_utils import domain_error_to_resource_payload, jsonify
from brew.water.service import WaterService


def register_water_mcp(mcp: FastMCP, service: WaterService) -> None:
    @mcp.resource(
        "coffee://water",
        description="Estimated water remaining in the 1500 mL jug and last-refill timestamp.",
    )
    async def get_water() -> str:
        try:
            water = await service.get_water()
        except DomainError as e:
            return domain_error_to_resource_payload(e)
        return jsonify(water)
