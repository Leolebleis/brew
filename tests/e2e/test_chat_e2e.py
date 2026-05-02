"""End-to-end chat backend tests.

Drives the full POST /chat/messages -> SSE stream -> assistant-row persistence
-> GET /chat/messages replay flow with pydantic-ai's TestModel as the LLM.
"""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import Mock

import pytest
from asgi_lifespan import LifespanManager
from fastmcp import FastMCP
from httpx import ASGITransport, AsyncClient
from pydantic_ai.models.test import TestModel

import brew.main
from brew.aiden.dependencies import get_aiden_settings
from brew.chat.config import get_chat_settings
from brew.chat.dependencies import get_chat_service
from brew.chat.model.event import TextDelta
from brew.dependencies import get_settings
from brew.errors import CloudUnreachableError
from brew.main import app
from tests._sse import parse_sse_async


@pytest.fixture
async def chat_e2e_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fellow_mock: Mock
) -> AsyncGenerator[AsyncClient]:
    db_path = tmp_path / "brew.db"
    monkeypatch.setenv("FELLOW_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("FELLOW_ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(brew.main, "_chat_enabled", True)
    monkeypatch.setattr(brew.main, "_mcp_enabled", True)
    mcp_server = FastMCP("test-mcp")
    monkeypatch.setattr(brew.main, "_mcp_server", mcp_server, raising=False)
    monkeypatch.setattr(brew.main, "_mcp_app", mcp_server.http_app(path="/"), raising=False)

    monkeypatch.setattr("brew.aiden.dependencies.build_fellow_client", lambda: fellow_mock)
    monkeypatch.setattr("brew.main.build_fellow_client", lambda: fellow_mock)

    get_settings.cache_clear()
    get_aiden_settings.cache_clear()
    get_chat_settings.cache_clear()

    async with LifespanManager(app) as manager:
        # After lifespan boot, swap the chat agent's underlying pydantic-ai
        # model with TestModel for the duration of this test.
        chat_service = app.dependency_overrides[get_chat_service]()
        with chat_service._agent.inner.override(  # noqa: SLF001
            model=TestModel(custom_output_text="Hello from the test model.", call_tools=[])
        ):
            transport = ASGITransport(app=manager.app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client


async def test_post_then_get_replays_turn(chat_e2e_client: AsyncClient) -> None:
    """Golden path: POST a message, consume SSE stream ending in `done`, then GET replays both rows."""
    async with chat_e2e_client.stream(
        "POST",
        "/api/chat/messages",
        json={"text": "hello"},
        headers={"X-API-Key": ""},
    ) as resp:
        assert resp.status_code == 200
        events = await parse_sse_async(resp.aiter_lines())

    event_names = [name for name, _ in events]
    assert event_names[-1] == "done"
    assert "text_delta" in event_names

    done_data = events[-1][1]
    assert "message_id" in done_data
    assistant_id = done_data["message_id"]

    # Replay
    resp = await chat_e2e_client.get("/api/chat/messages?limit=10", headers={"X-API-Key": ""})
    assert resp.status_code == 200
    body = resp.json()
    ids = [m["id"] for m in body["messages"]]
    assert assistant_id in ids
    kinds = [m["kind"] for m in body["messages"]]
    assert kinds.count("request") == 1
    assert kinds.count("response") == 1
    assert body["next_before_id"] is None  # only 2 rows, less than limit


async def test_mid_stream_error_persists_user_row_only(chat_e2e_client: AsyncClient) -> None:
    """Mid-stream agent failure: user-row stays, no assistant-row, SSE ends with `error`."""
    real_service = brew.main.app.dependency_overrides[get_chat_service]()

    class FlakyAgent:
        async def stream(self, prompt, history):  # noqa: ARG002
            yield TextDelta(text="partial...")
            raise CloudUnreachableError(message="anthropic timed out")

    real_service._agent = FlakyAgent()  # noqa: SLF001

    async with chat_e2e_client.stream(
        "POST",
        "/api/chat/messages",
        json={"text": "trigger failure"},
        headers={"X-API-Key": ""},
    ) as resp:
        assert resp.status_code == 200
        events = await parse_sse_async(resp.aiter_lines())

    event_names = [name for name, _ in events]
    assert "error" in event_names
    assert "done" not in event_names

    # User-row stayed; no assistant-row.
    resp = await chat_e2e_client.get("/api/chat/messages?limit=10", headers={"X-API-Key": ""})
    body = resp.json()
    kinds = [m["kind"] for m in body["messages"]]
    assert kinds.count("request") >= 1
    assert kinds.count("response") == 0
