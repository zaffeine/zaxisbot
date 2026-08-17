import os
import discord
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Comma-separated list of user IDs to DM, e.g. "111111111111111111,222222222222222222"
USER_IDS = [int(uid.strip()) for uid in os.getenv("DISCORD_USER_IDS").split(",")]

# Hardcoded sensitivities — replace with your actual user IDs and values.
SENSITIVITIES = {
    159754733689634816: {"dpi": 800, "sens": 0.9, "edpi": 800 * 0.9},   # you
    222222222222222222: {"dpi": 800, "sens": 0.8, "edpi": 800 * 0.8},     # friend
}


def format_sens(user_id):
    data = SENSITIVITIES.get(user_id)
    if data is None:
        return "your sens"
    return f"{data['dpi']} DPI / {data['sens']} in-game sens ({data['edpi']:.0f} eDPI)"

YES_EMOJI = "✅"
NO_EMOJI = "❌"

YES_MESSAGE = "🎯 Good kitty. Stay disciplined. Consistency is the whole game."
NO_MESSAGE = "🚨 CHANGE IT BACK, RIGHT NYEOW"

intents = discord.Intents.default()
intents.reactions = True  # covers both guild and DM reaction events
client = discord.Client(intents=intents)

# Maps active reminder message ID -> the user ID it was sent to,
# so we know which DM a reaction belongs to.
active_messages = {}


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    if not remind.is_running():
        remind.start()


@tasks.loop(hours=48)
async def remind():
    for user_id in USER_IDS:
        try:
            sens = format_sens(user_id)
            user = await client.fetch_user(user_id)
            message = await user.send(f"Are you still running {sens}?")
            await message.add_reaction(YES_EMOJI)
            await message.add_reaction(NO_EMOJI)
            active_messages[message.id] = user_id
        except discord.Forbidden:
            print(f"Could not DM user {user_id} — they may have DMs disabled or don't share a server with the bot.")


@client.event
async def on_raw_reaction_add(payload):
    # Ignore the bot's own reactions
    if payload.user_id == client.user.id:
        return

    # Only react to reactions on a currently-active reminder message
    if payload.message_id not in active_messages:
        return

    emoji = str(payload.emoji)
    user = await client.fetch_user(payload.user_id)
    sens = format_sens(payload.user_id)

    if emoji == YES_EMOJI:
        await user.send(f"{YES_MESSAGE} ({sens} locked in.)")
    elif emoji == NO_EMOJI:
        await user.send(f"{NO_MESSAGE} Get it back to {sens}.")


client.run(TOKEN)