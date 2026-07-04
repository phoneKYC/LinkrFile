"""
database.py — Async SQLite for settings and stats.
"""

import logging
import aiosqlite
from config import cfg

logger = logging.getLogger(__name__)

DB_PATH = cfg.db_path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_settings (
    chat_id  INTEGER PRIMARY KEY,
    language TEXT    NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS stats (
    key   TEXT PRIMARY KEY,
    value INTEGER NOT NULL DEFAULT 0
);
"""


async def get_settings(chat_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(_SCHEMA)
        async with db.execute(
            "SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)
        ) as cur:
            row = await cur.fetchone()
    if row:
        return dict(row)
    return {"chat_id": chat_id, "language": cfg.default_language}


async def save_settings(chat_id: int, **kwargs) -> None:
    current = await get_settings(chat_id)
    current.update(kwargs)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.execute(
            """
            INSERT INTO chat_settings (chat_id, language)
            VALUES (:chat_id, :language)
            ON CONFLICT(chat_id) DO UPDATE SET language = excluded.language
            """,
            current,
        )
        await db.commit()


async def stat_inc(key: str, amount: int = 1) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(_SCHEMA)
        await db.execute(
            """
            INSERT INTO stats (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = value + excluded.value
            """,
            (key, amount),
        )
        await db.commit()


async def stat_get(key: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(_SCHEMA)
        async with db.execute(
            "SELECT value FROM stats WHERE key = ?", (key,)
        ) as cur:
            row = await cur.fetchone()
    return row["value"] if row else 0


async def stat_all() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.executescript(_SCHEMA)
        async with db.execute("SELECT key, value FROM stats") as cur:
            rows = await cur.fetchall()
    return {r["key"]: r["value"] for r in rows}