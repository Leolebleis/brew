"""When the terminal feature is disabled (default), the WS endpoint must 404.

Regression: previously the chat router was registered unconditionally and
only the service was wired conditionally — calls 500'd with NotImplementedError
leaking. We now gate at the router level. Same shape, repointed at
/api/terminal/ws.
"""

from httpx import AsyncClient


async def test_terminal_ws_404_when_disabled(e2e_client: AsyncClient) -> None:
    # WebSocket upgrade requests carry GET semantics over httpx.ASGITransport.
    # Without the upgrade headers the route returns 404 because the gate runs
    # before WebSocket negotiation.
    response = await e2e_client.get("/api/terminal/ws")
    assert response.status_code == 404
