from datetime import UTC, datetime
from unittest.mock import AsyncMock

from brew.chat.model.message import ChatMessage, ChatMessageCreate
from brew.chat.service import ChatService


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
    service = ChatService(repo=repo, agent=AsyncMock())

    create = ChatMessageCreate(thread_id="t1", kind="request", payload={"role": "user"})
    result = await service.append_message(create)

    assert result is expected
    repo.append.assert_awaited_once_with(create)


async def test_get_thread_delegates_to_repo() -> None:
    expected = [_make_message()]
    repo = AsyncMock()
    repo.list_thread = AsyncMock(return_value=expected)
    service = ChatService(repo=repo, agent=AsyncMock())

    result = await service.get_thread("t1")

    assert result is expected
    repo.list_thread.assert_awaited_once_with("t1")


async def test_list_threads_delegates_to_repo() -> None:
    expected = ["t-new", "t-old"]
    repo = AsyncMock()
    repo.list_threads = AsyncMock(return_value=expected)
    service = ChatService(repo=repo, agent=AsyncMock())

    result = await service.list_threads()

    assert result == expected
    repo.list_threads.assert_awaited_once_with()
