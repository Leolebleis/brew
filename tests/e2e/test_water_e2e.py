"""E2E for the water bounded context — GET /water, POST /water/refill, real SQLite round-trip."""

from datetime import datetime

from httpx import AsyncClient


async def test_seeded_water_is_1500ml(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/water")
    assert response.status_code == 200
    data = response.json()
    assert data["remaining_ml"] == 1500


async def test_refill_resets_to_1500_after_simulated_drawdown(e2e_client: AsyncClient) -> None:
    before = (await e2e_client.get("/water")).json()
    before_ts = datetime.fromisoformat(before["last_refilled_at"])

    response = await e2e_client.post("/water/refill")
    assert response.status_code == 200

    after = (await e2e_client.get("/water")).json()
    after_ts = datetime.fromisoformat(after["last_refilled_at"])
    assert after["remaining_ml"] == 1500
    assert after_ts >= before_ts
