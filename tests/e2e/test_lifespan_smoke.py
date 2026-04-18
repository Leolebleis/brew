"""Smoke tests for the e2e fixture itself — verifies lifespan runs + fixture wiring works."""

from httpx import AsyncClient


async def test_health_endpoint_reachable_through_lifespan(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/health")
    assert response.status_code == 200


async def test_lifespan_ran_db_is_initialized(e2e_client: AsyncClient) -> None:
    """If the lifespan ran, water_state was seeded to 1500 mL by WATER_SCHEMA's INSERT OR IGNORE."""
    response = await e2e_client.get("/water")
    # The require_api_key guard is a no-op when FELLOW_API_KEY setting is None
    # (the default in tests). If this ever fails with 401, delete the
    # FELLOW_API_KEY env var via monkeypatch in the e2e_client fixture.
    assert response.status_code == 200
    data = response.json()
    assert data["remaining_ml"] == 1500
