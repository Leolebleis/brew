"""E2E for the bags bounded context — full CRUD + activate + zero through HTTP."""

from httpx import AsyncClient


def _payload(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": "Daybreak",
        "origin": "Ethiopia, Yirgacheffe",
        "roaster": "Intermission",
        "roast_level": "light",
        "initial_grams": 250,
        "profile_snapshot": {"ratio": 60.0, "bloom_duration": 30},
        "profile_id": "p-1",
    }
    base.update(overrides)
    return base


async def test_bag_crud_round_trip(e2e_client: AsyncClient) -> None:
    response = await e2e_client.post("/bags", json=_payload(name="First"))
    assert response.status_code == 201
    bag_id = response.json()["id"]

    get_response = await e2e_client.get(f"/bags/{bag_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "First"
    assert get_response.json()["remaining_grams"] == 250

    patch_response = await e2e_client.patch(f"/bags/{bag_id}", json={"name": "First Renamed"})
    assert patch_response.status_code == 200

    reloaded = (await e2e_client.get(f"/bags/{bag_id}")).json()
    assert reloaded["name"] == "First Renamed"

    delete_response = await e2e_client.delete(f"/bags/{bag_id}")
    assert delete_response.status_code == 204

    missing = await e2e_client.get(f"/bags/{bag_id}")
    assert missing.status_code == 404


async def test_bag_activate_swaps_active(e2e_client: AsyncClient) -> None:
    first = (await e2e_client.post("/bags", json=_payload(name="First"))).json()
    second = (await e2e_client.post("/bags", json=_payload(name="Second"))).json()

    r1 = await e2e_client.post(f"/bags/{first['id']}/activate")
    assert r1.status_code == 200

    r2 = await e2e_client.post(f"/bags/{second['id']}/activate")
    assert r2.status_code == 200

    first_reloaded = (await e2e_client.get(f"/bags/{first['id']}")).json()
    second_reloaded = (await e2e_client.get(f"/bags/{second['id']}")).json()
    assert first_reloaded["is_active"] is False
    assert second_reloaded["is_active"] is True


async def test_bag_zero_marks_finished(e2e_client: AsyncClient) -> None:
    bag = (await e2e_client.post("/bags", json=_payload())).json()
    await e2e_client.post(f"/bags/{bag['id']}/activate")

    response = await e2e_client.post(f"/bags/{bag['id']}/zero")
    assert response.status_code == 200

    reloaded = (await e2e_client.get(f"/bags/{bag['id']}")).json()
    assert reloaded["remaining_grams"] == 0
    assert reloaded["is_active"] is False
    assert reloaded["finished_at"] is not None


async def test_list_filter_by_roaster(e2e_client: AsyncClient) -> None:
    await e2e_client.post("/bags", json=_payload(name="A", roaster="Intermission"))
    await e2e_client.post("/bags", json=_payload(name="B", roaster="Onyx"))

    response = await e2e_client.get("/bags?roaster=Onyx")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["name"] == "B"
