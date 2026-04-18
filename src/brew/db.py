"""SQLite connection + schema initialization helpers.

Each bounded context that needs persistence exposes a `SCHEMA: list[str]` of DDL
statements. `main.py` assembles all of them and passes to `init_db` during the
app lifespan.
"""

import aiosqlite


async def open_db(path: str) -> aiosqlite.Connection:
    """Open a SQLite connection with pragmas tuned for this app."""
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA foreign_keys = ON")
    return conn


async def init_db(conn: aiosqlite.Connection, schemas: list[list[str]]) -> None:
    """Execute every DDL statement in every schema list, then commit."""
    for schema in schemas:
        for ddl in schema:
            await conn.execute(ddl)
    await conn.commit()
