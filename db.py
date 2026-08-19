"""
SQLite persistence layer for Mjautomat.

Stores per-Discord-user data: linked Steam ID, CS2 settings, and the
state needed to run periodic sens-check reminders. No secrets live here —
the bot token stays in .env.
"""

import aiosqlite
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).parent / "mjautomat.db"

_conn: aiosqlite.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    discord_id INTEGER PRIMARY KEY,
    steam_id TEXT,
    dpi INTEGER,
    sens REAL,
    resolution TEXT,
    crosshair TEXT,
    reminder_enabled INTEGER NOT NULL DEFAULT 0,
    reminder_interval_hours INTEGER NOT NULL DEFAULT 48,
    last_reminder_time TEXT,
    awaiting_reply INTEGER NOT NULL DEFAULT 0,
    invalid_streak INTEGER NOT NULL DEFAULT 0
);
"""

UPDATABLE_FIELDS = {"steam_id", "dpi", "sens", "resolution", "crosshair"}


def _now_sql() -> str:
    # Naive UTC string in a format SQLite's datetime() functions understand.
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


async def init_db():
    global _conn
    _conn = await aiosqlite.connect(DB_PATH)
    _conn.row_factory = aiosqlite.Row
    await _conn.execute(SCHEMA)
    await _conn.commit()


async def close_db():
    if _conn is not None:
        await _conn.close()


async def ensure_user(discord_id: int):
    await _conn.execute(
        "INSERT OR IGNORE INTO users (discord_id) VALUES (?)", (discord_id,)
    )
    await _conn.commit()


async def get_user(discord_id: int) -> dict | None:
    async with _conn.execute(
        "SELECT * FROM users WHERE discord_id = ?", (discord_id,)
    ) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def update_settings(discord_id: int, **fields) -> None:
    """Update only the provided, non-None fields for a user."""
    fields = {k: v for k, v in fields.items() if k in UPDATABLE_FIELDS and v is not None}
    if not fields:
        return
    await ensure_user(discord_id)
    columns = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [discord_id]
    await _conn.execute(f"UPDATE users SET {columns} WHERE discord_id = ?", values)
    await _conn.commit()


async def set_reminder_state(discord_id: int, enabled: bool, interval_hours: int | None = None) -> None:
    await ensure_user(discord_id)
    if interval_hours is not None:
        await _conn.execute(
            "UPDATE users SET reminder_enabled = ?, reminder_interval_hours = ? WHERE discord_id = ?",
            (int(enabled), interval_hours, discord_id),
        )
    else:
        await _conn.execute(
            "UPDATE users SET reminder_enabled = ? WHERE discord_id = ?",
            (int(enabled), discord_id),
        )
    await _conn.commit()


async def get_due_reminder_users() -> list[dict]:
    """Users whose reminder is enabled, not currently awaiting a reply,
    and whose interval has elapsed since their last reminder (or who
    have never been reminded yet)."""
    query = """
        SELECT * FROM users
        WHERE reminder_enabled = 1
        AND awaiting_reply = 0
        AND (
            last_reminder_time IS NULL
            OR datetime(last_reminder_time) <= datetime('now', '-' || reminder_interval_hours || ' hours')
        )
    """
    async with _conn.execute(query) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def mark_reminder_sent(discord_id: int) -> None:
    await _conn.execute(
        "UPDATE users SET last_reminder_time = ?, awaiting_reply = 1, invalid_streak = 0 WHERE discord_id = ?",
        (_now_sql(), discord_id),
    )
    await _conn.commit()


async def clear_awaiting(discord_id: int) -> None:
    await _conn.execute(
        "UPDATE users SET awaiting_reply = 0, invalid_streak = 0 WHERE discord_id = ?",
        (discord_id,),
    )
    await _conn.commit()


async def increment_invalid_streak(discord_id: int) -> int:
    """Returns the streak value *before* incrementing, so callers can use
    it directly as an index into an escalation ladder."""
    async with _conn.execute(
        "SELECT invalid_streak FROM users WHERE discord_id = ?", (discord_id,)
    ) as cur:
        row = await cur.fetchone()
    current = row["invalid_streak"] if row else 0
    await _conn.execute(
        "UPDATE users SET invalid_streak = ? WHERE discord_id = ?", (current + 1, discord_id)
    )
    await _conn.commit()
    return current
