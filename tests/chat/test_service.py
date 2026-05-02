from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from brew.chat.model.event import (
    AgentDone,
    Done,
    Error,
    TextDelta,
)
from brew.chat.model.message import ChatMessage, ChatMessageCreate
from brew.chat.service import ChatService
from brew.errors import NotFoundError
from tests.chat.conftest import make_fake_chat_agent


def _make_message(**overrides: object) -> ChatMessage:
    defaults: dict[str, object] = {
        "id": "m1",
        "thread_id": "t1",
        "kind": "request",
        "payload": {"role": "user"},
        "created_at": datetime(2026, 4, 19, 8, 30, tzinfo=UTC),
    }
    defaults.update(overrides)
    return ChatMessage(**defaults)  # type: ignore[arg-type]


async def test_append_message_delegates_to_repo() -> None:
    expected = _make_message()
    repo = AsyncMock()
    repo.append = AsyncMock(return_value=expected)
    service = ChatService(repo=repo, agent=make_fake_chat_agent([]))

    create = ChatMessageCreate(thread_id="t1", kind="request", payload={"role": "user"})
    result = await service.append_message(create)

    assert result is expected
    repo.append.assert_awaited_once_with(create)


async def test_list_threads_delegates_to_repo() -> None:
    expected = ["t-new", "t-old"]
    repo = AsyncMock()
    repo.list_threads = AsyncMock(return_value=expected)
    service = ChatService(repo=repo, agent=make_fake_chat_agent([]))

    result = await service.list_threads()

    assert result == expected
    repo.list_threads.assert_awaited_once_with()


async def test_stream_message_writes_user_row_then_yields_done() -> None:
    repo = AsyncMock()
    repo.load_history = AsyncMock(return_value=[])
    user_msg = _make_message(id="user-id", kind="request")
    asst_msg = _make_message(id="asst-id", kind="response")
    repo.append = AsyncMock(side_effect=[user_msg, asst_msg])

    agent = make_fake_chat_agent(
        [
            TextDelta(text="Hello "),
            TextDelta(text="world"),
            AgentDone(payload={"role": "model", "parts": []}),
        ]
    )
    service = ChatService(repo=repo, agent=agent)

    events = [ev async for ev in service.stream_message("default", "hi")]

    # Two repo.append calls: user-row first, assistant-row last.
    assert repo.append.await_count == 2
    first_call_kind = repo.append.await_args_list[0].args[0].kind
    second_call_kind = repo.append.await_args_list[1].args[0].kind
    assert first_call_kind == "request"
    assert second_call_kind == "response"

    # Yielded events: TextDelta x2 then Done (NOT AgentDone — translated).
    assert isinstance(events[0], TextDelta)
    assert isinstance(events[1], TextDelta)
    assert isinstance(events[2], Done)
    assert events[2].message_id == "asst-id"


async def test_stream_message_on_mid_stream_error_keeps_user_row_no_assistant_row() -> None:
    repo = AsyncMock()
    repo.load_history = AsyncMock(return_value=[])
    user_msg = _make_message(id="user-id", kind="request")
    repo.append = AsyncMock(return_value=user_msg)

    # Agent raises after yielding one event.
    agent = make_fake_chat_agent(
        [TextDelta(text="partial...")],
        raise_after=1,
    )
    service = ChatService(repo=repo, agent=agent)

    events = [ev async for ev in service.stream_message("default", "hi")]

    # Exactly one append (the user-row).
    assert repo.append.await_count == 1
    assert repo.append.await_args_list[0].args[0].kind == "request"

    # Yielded events: TextDelta then Error.
    assert isinstance(events[0], TextDelta)
    assert isinstance(events[-1], Error)
    assert events[-1].code == "cloud_unreachable"


async def test_stream_message_history_is_loaded_and_forwarded() -> None:
    repo = AsyncMock()
    history_msg = _make_message(id="prior", kind="response", payload={"prior": True})
    repo.load_history = AsyncMock(return_value=[history_msg])

    captured: dict = {}

    class _CapturingAgent:
        async def stream(self, prompt, history):
            captured["prompt"] = prompt
            captured["history"] = history
            yield AgentDone(payload={"role": "model"})

    repo.append = AsyncMock(side_effect=[_make_message(id="u"), _make_message(id="a")])
    service = ChatService(repo=repo, agent=_CapturingAgent())

    [ev async for ev in service.stream_message("default", "test prompt")]

    assert captured["prompt"] == "test prompt"
    assert captured["history"] == [{"prior": True}]


async def test_get_thread_no_cursor_returns_messages_and_no_next() -> None:
    repo = AsyncMock()
    repo.list_thread = AsyncMock(return_value=[_make_message(id="m1")])
    service = ChatService(repo=repo, agent=make_fake_chat_agent([]))

    messages, next_before = await service.get_thread("default", limit=10)

    assert [m.id for m in messages] == ["m1"]
    assert next_before is None
    repo.list_thread.assert_awaited_once_with("default", limit=10, before=None)


async def test_get_thread_full_page_returns_next_before_id() -> None:
    repo = AsyncMock()
    msgs = [_make_message(id=f"m{i}") for i in range(3)]
    repo.list_thread = AsyncMock(return_value=msgs)
    service = ChatService(repo=repo, agent=make_fake_chat_agent([]))

    messages, next_before = await service.get_thread("default", limit=3)

    assert [m.id for m in messages] == ["m0", "m1", "m2"]
    assert next_before == "m2"  # oldest in the page


async def test_get_thread_unknown_before_id_raises_not_found() -> None:
    repo = AsyncMock()
    repo.get_message = AsyncMock(return_value=None)
    service = ChatService(repo=repo, agent=make_fake_chat_agent([]))

    with pytest.raises(NotFoundError) as exc_info:
        await service.get_thread("default", limit=10, before_id="missing-uuid")

    assert exc_info.value.resource_kind == "chat_message"
    assert exc_info.value.resource_id == "missing-uuid"
