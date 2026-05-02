import pytest

from brew.chat.model.message import ChatMessageCreate
from brew.chat.repository import ChatSqliteRepository
from brew.chat.schema import CHAT_SCHEMA
from brew.datetime_utils import to_iso
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


async def test_get_message_returns_existing(repo: ChatSqliteRepository) -> None:
    created = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 1}))
    fetched = await repo.get_message(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.payload == {"i": 1}


async def test_get_message_returns_none_for_unknown(repo: ChatSqliteRepository) -> None:
    fetched = await repo.get_message("does-not-exist")
    assert fetched is None


async def test_list_thread_returns_newest_first(repo: ChatSqliteRepository) -> None:
    first = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 1}))
    second = await repo.append(ChatMessageCreate(thread_id="t1", kind="response", payload={"i": 2}))
    third = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 3}))

    messages = await repo.list_thread("t1", limit=10)

    assert [m.id for m in messages] == [third.id, second.id, first.id]


async def test_list_thread_respects_limit(repo: ChatSqliteRepository) -> None:
    ids = []
    for i in range(5):
        msg = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": i}))
        ids.append(msg.id)

    page = await repo.list_thread("t1", limit=2)
    assert len(page) == 2
    assert [m.id for m in page] == [ids[4], ids[3]]


async def test_list_thread_empty_for_unknown_id(repo: ChatSqliteRepository) -> None:
    messages = await repo.list_thread("does-not-exist", limit=10)
    assert messages == []


async def test_list_thread_before_excludes_cursor_row(repo: ChatSqliteRepository) -> None:
    """Verify the (created_at, rowid) row-value comparison correctly excludes the cursor row.

    Uses raw rowid lookup since the public API doesn't expose it — this is a repo-level
    invariant test only; consumers go through the service layer's get_message → cursor path.
    """
    msgs = [await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": i})) for i in range(5)]

    # Find the rowid of msgs[3] via a raw query.
    cursor = await repo._conn.execute("SELECT rowid FROM chat_messages WHERE id = ?", (msgs[3].id,))  # noqa: SLF001
    row = await cursor.fetchone()
    assert row is not None
    rowid_3 = row["rowid"]

    page = await repo.list_thread(
        "t1",
        limit=10,
        before=(to_iso(msgs[3].created_at), rowid_3),
    )
    # Should return msgs[2], msgs[1], msgs[0] — strictly older than msgs[3].
    assert [m.id for m in page] == [msgs[2].id, msgs[1].id, msgs[0].id]


async def test_list_threads_returns_distinct_ids_recent_first(repo: ChatSqliteRepository) -> None:
    await repo.append(ChatMessageCreate(thread_id="t-old", kind="request", payload={}))
    await repo.append(ChatMessageCreate(thread_id="t-old", kind="response", payload={}))
    await repo.append(ChatMessageCreate(thread_id="t-new", kind="request", payload={}))

    threads = await repo.list_threads()

    assert threads == ["t-new", "t-old"]


async def test_load_history_returns_oldest_first(repo: ChatSqliteRepository) -> None:
    first = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 1}))
    second = await repo.append(ChatMessageCreate(thread_id="t1", kind="response", payload={"i": 2}))
    third = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": 3}))

    history = await repo.load_history("t1")

    assert [m.id for m in history] == [first.id, second.id, third.id]


async def test_load_history_truncates_to_max_messages_keeping_recent(repo: ChatSqliteRepository) -> None:
    ids = []
    for i in range(10):
        msg = await repo.append(ChatMessageCreate(thread_id="t1", kind="request", payload={"i": i}))
        ids.append(msg.id)

    history = await repo.load_history("t1", max_messages=3)

    # Oldest-first, but truncated to the most recent 3.
    assert [m.id for m in history] == [ids[7], ids[8], ids[9]]
