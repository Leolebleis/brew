"""When chat is disabled (default), the chat router must not be reachable.

Regression: previously the router was registered unconditionally and only the
service was wired conditionally — calls 500'd with `NotImplementedError`
leaking from the unoverridden dependency stub. Disabled chat should be a
clean 404, not a 500.
"""

from httpx import AsyncClient


async def test_post_chat_messages_404_when_disabled(e2e_client: AsyncClient) -> None:
    response = await e2e_client.post("/api/chat/messages", json={"text": "hi"})
    assert response.status_code == 404


async def test_get_chat_messages_404_when_disabled(e2e_client: AsyncClient) -> None:
    response = await e2e_client.get("/api/chat/messages")
    assert response.status_code == 404
