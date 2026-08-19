# Mjautomat

A small, modular, mildly hostile Discord gaming bot. Started as a
CS2 sens-check reminder for two people, now backed by SQLite so it can
grow.

## Structure

```
mjautomat/
├── bot.py              entry point
├── db.py                SQLite persistence layer
├── personality.py       shared tone/message pools
├── migrate_legacy.py    one-off script to import the old hardcoded users
├── requirements.txt
├── .env.example
└── cogs/
    ├── settings.py       /settings set, /settings show
    ├── reminders.py      /remindme on|off, background loop, DM yes/no handling
    ├── steam.py          /steam link, /steam show
    └── inventory.py      /inventory
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:
```
DISCORD_TOKEN=your_bot_token_here
STEAM_API_KEY=your_steam_web_api_key_here   # optional, only needed for /steam and /inventory
```

Get a Steam Web API key (free) at https://steamcommunity.com/dev/apikey
if you want `/steam` and `/inventory` to work. Without it, those two
commands will just tell the user no key is configured — everything else
works fine.

## Migrating your old hardcoded two-user setup

If you're coming from the old single-file script with a hardcoded
`SENSITIVITIES` dict, edit `migrate_legacy.py` with your real Discord
user IDs, DPI, and sens, then run it once:

```bash
python migrate_legacy.py
```

This seeds the database and turns reminders on for those users at 48h.
You can delete the script afterward — the bot itself never touches it.

## Running

```bash
python bot.py
```

Slash commands sync automatically on startup (`setup_hook` calls
`tree.sync()`). It can take up to an hour for global command syncs to
propagate the first time on Discord's end, though it's usually much
faster.

## Commands

- `/settings set [dpi] [sens] [resolution] [crosshair]` — update your own settings (any subset)
- `/settings show [member]` — view your own or someone else's settings
- `/remindme on [interval_hours]` — opt into periodic sens-check DMs (default 48h)
- `/remindme off` — opt out
- `/steam link <steam_id_or_vanity>` — link your Steam account
- `/steam show [member]` — show current/last-played game for a linked account
- `/inventory [member]` — summarize a linked CS2 inventory (requires a public inventory)

## Sens-check flow

Every 30 minutes, a background loop checks who's due for a reminder
based on their own interval. When due, Mjautomat DMs:

> Are you still running 800 DPI / 0.9 in-game sens (720 eDPI)? (reply yes or no)

- **yes** → random pick from a pool of approving one-liners ("Good kitty.", "Acceptable.", ...)
- **no** → random pick from a pool of hostile one-liners, plus the eDPI to revert to
- **anything else** → an escalating annoyance ladder, from a polite nudge
  down to just "gonk" — resets each time a new question goes out or the
  user finally answers correctly

## Extending

Everything Steam/CS2-related lives in its own cog and its own aiohttp
session, so adding FACEIT stats or match history later just means a new
`cogs/faceit.py` following the same pattern — a `commands.Cog` subclass,
an `app_commands.Group` or standalone `app_commands.command`, and an
async `setup(bot)` function. Add the new module to `EXTENSIONS` in
`bot.py` and it's live.

The `users` table in `db.py` already has room to grow — adding a
sensitivity-change history table later is just a new `CREATE TABLE` in
`SCHEMA` plus a couple of helper functions.
