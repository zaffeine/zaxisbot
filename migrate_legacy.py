"""
One-off script to migrate the old hardcoded two-user sens/reminder setup
into the new SQLite-backed system.

Edit LEGACY_USERS below to match your old SENSITIVITIES dict and desired
reminder interval, then run:

    python migrate_legacy.py

Safe to delete once you've run it — the bot itself never calls this.
"""

import asyncio

import db

LEGACY_USERS = {
    159754733689634816: {"dpi": 800, "sens": 0.9, "interval_hours": 48},  # you
    # 222222222222222222: {"dpi": 800, "sens": 0.8, "interval_hours": 48},  # friend
}


async def main():
    await db.init_db()
    for discord_id, settings in LEGACY_USERS.items():
        await db.update_settings(discord_id, dpi=settings["dpi"], sens=settings["sens"])
        await db.set_reminder_state(discord_id, enabled=True, interval_hours=settings["interval_hours"])
        print(f"Migrated {discord_id}: dpi={settings['dpi']} sens={settings['sens']} reminders=ON")
    await db.close_db()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
