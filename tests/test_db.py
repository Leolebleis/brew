from brew.db import init_db, open_db


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
