import aiosqlite

from brew.db import add_missing_columns, init_db, open_db


async def test_open_db_returns_connection_with_foreign_keys_on() -> None:
    conn = await open_db(":memory:")
    try:
        cursor = await conn.execute("PRAGMA foreign_keys")
        row = await cursor.fetchone()
        assert row[0] == 1
    finally:
        await conn.close()


async def test_init_db_runs_registered_ddl() -> None:
    conn = await open_db(":memory:")
    try:
        await init_db(conn, [["CREATE TABLE demo (id INTEGER PRIMARY KEY, name TEXT)"]])
        await conn.execute("INSERT INTO demo (name) VALUES ('x')")
        await conn.commit()
        cursor = await conn.execute("SELECT name FROM demo")
        row = await cursor.fetchone()
        assert row[0] == "x"
    finally:
        await conn.close()


async def test_init_db_runs_multiple_schema_lists() -> None:
    conn = await open_db(":memory:")
    try:
        await init_db(
            conn,
            [
                ["CREATE TABLE a (id INTEGER)"],
                ["CREATE TABLE b (id INTEGER)"],
            ],
        )
        cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        rows = await cursor.fetchall()
        assert [r[0] for r in rows] == ["a", "b"]
    finally:
        await conn.close()


async def test_add_missing_columns_adds_only_absent_ones() -> None:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("CREATE TABLE t (id TEXT PRIMARY KEY, a TEXT)")
    await conn.execute("INSERT INTO t (id, a) VALUES ('1', 'x')")
    await conn.commit()

    await add_missing_columns(conn, "t", {"a": "TEXT", "b": "INTEGER", "c": "TEXT NOT NULL DEFAULT '[]'"})

    cursor = await conn.execute("PRAGMA table_info(t)")
    cols = {row["name"] for row in await cursor.fetchall()}
    assert {"id", "a", "b", "c"} <= cols

    cursor = await conn.execute("SELECT b, c FROM t WHERE id = '1'")
    row = await cursor.fetchone()
    assert row["b"] is None
    assert row["c"] == "[]"
    await conn.close()


async def test_add_missing_columns_is_idempotent() -> None:
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.execute("CREATE TABLE t (id TEXT PRIMARY KEY)")
    await conn.commit()
    await add_missing_columns(conn, "t", {"b": "INTEGER"})
    await add_missing_columns(conn, "t", {"b": "INTEGER"})  # must not raise
    cursor = await conn.execute("PRAGMA table_info(t)")
    assert {row["name"] for row in await cursor.fetchall()} == {"id", "b"}
    await conn.close()
