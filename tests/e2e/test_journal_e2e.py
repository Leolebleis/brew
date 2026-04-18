"""E2E for the journal bounded context — read-path only.

Creation is internal (Phase 2 BrewCompleted subscriber). Full end-to-end
create→rate→browse coverage arrives with that phase.
"""

from httpx import AsyncClient


async def test_empty_journal_returns_empty_list(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/journal")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_missing_entry_returns_404(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/journal/does-not-exist")
    assert response.status_code == 404


async def test_patch_missing_entry_returns_404(e2e_client: AsyncClient) -> None:
    response = await e2e_client.patch("/journal/does-not-exist", json={"rating": 4})
    assert response.status_code == 404


async def test_delete_missing_entry_returns_404(e2e_client: AsyncClient) -> None:
    response = await e2e_client.delete("/journal/does-not-exist")
    assert response.status_code == 404


async def test_list_filter_params_accepted(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/journal?bag_id=b1&rating_min=4")
    assert response.status_code == 200
    assert response.json() == []


async def test_patch_rating_out_of_range_returns_422(e2e_client: AsyncClient) -> None:
    response = await e2e_client.patch("/journal/any-id", json={"rating": 10})
    assert response.status_code == 422


async def test_no_public_post_endpoint(e2e_client: AsyncClient) -> None:
    response = await e2e_client.post("/journal", json={})
    assert response.status_code in {404, 405}
