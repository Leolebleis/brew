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


async def add_missing_columns(conn: aiosqlite.Connection, table: str, columns: dict[str, str]) -> None:
    """Additively ALTER in any columns not already present on `table`.

    SQLite has no `ADD COLUMN IF NOT EXISTS`, so we diff against PRAGMA table_info.
    `columns` maps column name -> the DDL type/constraint fragment, e.g.
    {"varietal": "TEXT", "acidity": "INTEGER CHECK (acidity IS NULL OR acidity BETWEEN -2 AND 2)"}.
    """
    cursor = await conn.execute(f"PRAGMA table_info({table})")
    existing = {row["name"] for row in await cursor.fetchall()}
    for name, ddl in columns.items():
        if name not in existing:
            await conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")
    await conn.commit()
