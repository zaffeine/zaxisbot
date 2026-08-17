import os
import random
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
    222222222222222222: {"dpi": 800, "sens": 0.8, "edpi": 800 * 0.8},   # friend
}


def format_sens(user_id):
    data = SENSITIVITIES.get(user_id)
    if data is None:
        return "your sens"
    return f"{data['dpi']} DPI / {data['sens']} in-game sens ({data['edpi']:.0f} eDPI)"


YES_MESSAGES = [
    "Good kitty.",
    "Acceptable.",
    "Good. Do not touch it.",
    "Configuration stable. Good kitty.",
    "Sens incident avoided.",
    "Very good. Carry on.",
]

NO_MESSAGES = [
    "CHANGE IT BACK, RIGHT NYEOW!!!!",
    "What the fuck did I tell you.",
    "0 DAYS SINCE LAST SENS INCIDENT.",
    "PUT IT BACK.",
    "You had ONE job.",
    "Revert your settings immediately.",
]

# Escalating patience for repeated invalid answers, keyed by how many
# invalid replies this person has sent since their last valid answer.
INVALID_ESCALATION = [
    "Please answer YES or NO.",
    "I said YES or NO.",
    "there are TWO OPTIONS",
    "u r gonk",
]
INVALID_ESCALATION_FINAL = "gonk"

intents = discord.Intents.default()
intents.message_content = True  # needed to read the text of DM replies
client = discord.Client(intents=intents)

# Tracks which user IDs currently have a pending question awaiting a yes/no reply.
awaiting_reply = set()

# Tracks how many invalid replies each user has sent in a row since their
# last valid yes/no answer — used to escalate the "patience" messages.
invalid_streak = {}


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
            await user.send(f"Are you still running {sens}? (reply yes or no)")
            awaiting_reply.add(user_id)
            invalid_streak[user_id] = 0
        except discord.Forbidden:
            print(f"Could not DM user {user_id} — they may have DMs disabled or don't share a server with the bot.")


@client.event
async def on_message(message):
    # Ignore the bot's own messages
    if message.author.id == client.user.id:
        return

    # Only handle direct messages, not server messages
    if not isinstance(message.channel, discord.DMChannel):
        return

    # Only respond if this person actually has a pending question
    if message.author.id not in awaiting_reply:
        return

    content = message.content.strip().lower()
    edpi = SENSITIVITIES[message.author.id]["edpi"]

    if content == "yes":
        await message.channel.send(random.choice(YES_MESSAGES))
        awaiting_reply.discard(message.author.id)
        invalid_streak.pop(message.author.id, None)
    elif content == "no":
        await message.channel.send(f"{random.choice(NO_MESSAGES)} Get it back to {edpi:.0f} eDPI")
        awaiting_reply.discard(message.author.id)
        invalid_streak.pop(message.author.id, None)
    else:
        streak = invalid_streak.get(message.author.id, 0)
        if streak < len(INVALID_ESCALATION):
            reply = INVALID_ESCALATION[streak]
        else:
            reply = INVALID_ESCALATION_FINAL
        invalid_streak[message.author.id] = streak + 1
        await message.channel.send(reply)


client.run(TOKEN)