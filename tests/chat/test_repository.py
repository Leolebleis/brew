import pytest

from brew.chat.model.message import ChatMessageCreate
from brew.chat.repository import ChatSqliteRepository
from brew.chat.schema import CHAT_SCHEMA
from brew.db import init_db, open_db


@pytest.fixture
async def repo():
    conn = await open_db(":memory:")
    await init_db(conn, [CHAT_SCHEMA])
    yield ChatSqliteRepository(conn=conn)
    await conn.close()


async def test_append_returns_full_entity(repo: ChatSqliteRepository) -> None:
    payload = {"role": "user", "content": [{"text": "hello"}]}
    msg = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload=payload))

    assert msg.id  # uuid string
    assert msg.thread_id == "t1"
    assert msg.kind == "request"
    assert msg.payload == payload  # round-trip
    assert msg.created_at is not None


async def test_list_thread_orders_by_insertion(repo: ChatSqliteRepository) -> None:
    first = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 1}))
    second = await repo.append(ChatMessageCreate(thread_id="t1", kind="response", payload={"i": 2}))
    third = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 3}))

    messages = await repo.list_thread("t1")

    assert [m.id for m in messages] == [first.id, second.id, third.id]


async def test_list_thread_empty_for_unknown_id(repo: ChatSqliteRepository) -> None:
    messages = await repo.list_thread("does-not-exist")
    assert messages == []


async def test_list_threads_returns_distinct_ids_recent_first(repo: ChatSqliteRepository) -> None:
    await repo.append(ChatMessageCreate(thread_id="t-old", kind="request", payload={}))
    await repo.append(ChatMessageCreate(thread_id="t-old", kind="response", payload={}))
    await repo.append(ChatMessageCreate(thread_id="t-new", kind="request", payload={}))

    threads = await repo.list_threads()

    assert threads == ["t-new", "t-old"]
