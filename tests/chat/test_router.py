"""Chat router tests — POST SSE + GET JSON via TestClient."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from brew.chat.dependencies import get_chat_service
from brew.chat.model.event import (
    Done,
    Error,
    TextDelta,
    ToolCallDelta,
    ToolCallResult,
    ToolCallStart,
)
from brew.chat.model.message import ChatMessage
from brew.errors import NotFoundError
from brew.main import app
from tests._sse import parse_sse


def _make_message(**overrides) -> ChatMessage:
    defaults: dict = {
        "id": "m1",
        "thread_id": "default",
        "kind": "request",
        "payload": {"role": "user"},
        "created_at": datetime(2026, 5, 2, 12, 0, tzinfo=UTC),
    }
    defaults.update(overrides)
    return ChatMessage(**defaults)


@pytest.fixture
def mock_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _override_service(mock_service: AsyncMock):
    app.dependency_overrides[get_chat_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(get_chat_service, None)


def _scripted_stream(events: list):
    async def gen(thread_id: str, text: str):  # noqa: ARG001
        for ev in events:
            yield ev

    return gen


async def test_post_text_only_emits_text_deltas_then_done(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.stream_message = _scripted_stream(
        [
            TextDelta(text="Hello "),
            TextDelta(text="world"),
            Done(message_id="asst-1"),
        ]
    )

    async with client.stream("POST", "/chat/messages", json={"text": "hi"}) as resp:
        assert resp.status_code == 200
        body = "".join([chunk async for chunk in resp.aiter_text()])

    events = parse_sse(body.splitlines())
    names = [n for n, _ in events]
    assert names == ["text_delta", "text_delta", "done"]
    assert events[-1][1] == {"message_id": "asst-1"}


async def test_post_with_tool_emits_tool_call_sequence(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.stream_message = _scripted_stream(
        [
            TextDelta(text="Let me check..."),
            ToolCallStart(tool_call_id="c1", tool_name="brew_now"),
            ToolCallDelta(tool_call_id="c1", args_delta='{"profile_id":'),
            ToolCallDelta(tool_call_id="c1", args_delta='"x"}'),
            ToolCallResult(tool_call_id="c1", result={"ok": True}),
            TextDelta(text="Done."),
            Done(message_id="asst-1"),
        ]
    )

    async with client.stream("POST", "/chat/messages", json={"text": "brew now"}) as resp:
        body = "".join([chunk async for chunk in resp.aiter_text()])

    events = parse_sse(body.splitlines())
    names = [n for n, _ in events]
    assert names == [
        "text_delta",
        "tool_call_start",
        "tool_call_delta",
        "tool_call_delta",
        "tool_call_result",
        "text_delta",
        "done",
    ]
    assert events[1][1] == {"tool_call_id": "c1", "tool_name": "brew_now"}
    assert events[4][1] == {"tool_call_id": "c1", "result": {"ok": True}}


async def test_post_mid_stream_error_ends_with_error_no_done(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.stream_message = _scripted_stream(
        [
            TextDelta(text="partial..."),
            Error(code="cloud_unreachable", message="anthropic timed out"),
        ]
    )

    async with client.stream("POST", "/chat/messages", json={"text": "hi"}) as resp:
        body = "".join([chunk async for chunk in resp.aiter_text()])

    events = parse_sse(body.splitlines())
    names = [n for n, _ in events]
    assert "error" in names
    assert "done" not in names
    error_event = next(d for n, d in events if n == "error")
    assert error_event["code"] == "cloud_unreachable"


async def test_post_empty_text_returns_422(client: AsyncClient) -> None:
    resp = await client.post("/chat/messages", json={"text": ""})
    assert resp.status_code == 422


async def test_get_no_cursor_returns_messages_and_next_before_id(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    msgs = [_make_message(id=f"m{i}") for i in range(3)]
    mock_service.get_thread = AsyncMock(return_value=(msgs, "m2"))

    resp = await client.get("/chat/messages?limit=3")

    assert resp.status_code == 200
    body = resp.json()
    assert [m["id"] for m in body["messages"]] == ["m0", "m1", "m2"]
    assert body["next_before_id"] == "m2"
    mock_service.get_thread.assert_awaited_once_with("default", limit=3, before_id=None)


async def test_get_with_before_id_passes_through(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.get_thread = AsyncMock(return_value=([], None))

    await client.get("/chat/messages?limit=10&before_id=some-uuid")

    mock_service.get_thread.assert_awaited_once_with("default", limit=10, before_id="some-uuid")


async def test_get_unknown_before_id_returns_404(
    client: AsyncClient,
    mock_service: AsyncMock,
) -> None:
    mock_service.get_thread.side_effect = NotFoundError.for_resource("chat_message", "foo")

    resp = await client.get("/chat/messages?before_id=foo")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "not_found"
    assert body["error"]["context"]["resource_id"] == "foo"


async def test_get_default_limit_50(client: AsyncClient, mock_service: AsyncMock) -> None:
    mock_service.get_thread = AsyncMock(return_value=([], None))

    await client.get("/chat/messages")

    mock_service.get_thread.assert_awaited_once_with("default", limit=50, before_id=None)


async def test_get_limit_over_max_returns_422(client: AsyncClient) -> None:
    resp = await client.get("/chat/messages?limit=999")
    assert resp.status_code == 422
