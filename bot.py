import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

EXTENSIONS = (
    "cogs.settings",
    "cogs.reminders",
    "cogs.steam",
    "cogs.inventory",
)

intents = discord.Intents.default()
intents.message_content = True  # needed to read yes/no/invalid text in DMs


class Mjautomat(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await db.init_db()
        for ext in EXTENSIONS:
            await self.load_extension(ext)
        await self.tree.sync()

    async def close(self):
        await db.close_db()
        await super().close()


bot = Mjautomat()


@bot.event
async def on_ready():
    print(f"Mjautomat online as {bot.user}")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set. Check your .env file.")
    bot.run(TOKEN)
