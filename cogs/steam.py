import os

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import db

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_API_BASE = "https://api.steampowered.com"


async def resolve_steam_id(session: aiohttp.ClientSession, identifier: str) -> str | None:
    identifier = identifier.strip()
    if identifier.isdigit() and len(identifier) == 17:
        return identifier

    url = f"{STEAM_API_BASE}/ISteamUser/ResolveVanityURL/v1/"
    params = {"key": STEAM_API_KEY, "vanityurl": identifier}
    async with session.get(url, params=params) as resp:
        if resp.status != 200:
            return None
        data = await resp.json()
    result = data.get("response", {})
    if result.get("success") == 1:
        return result.get("steamid")
    return None


class SteamCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    steam_group = app_commands.Group(name="steam", description="Link and view Steam info")

    @steam_group.command(name="link", description="Link your Steam account")
    @app_commands.describe(steam_id_or_vanity="Your SteamID64 or custom profile URL name")
    async def link(self, interaction: discord.Interaction, steam_id_or_vanity: str):
        if not STEAM_API_KEY:
            await interaction.response.send_message(
                "No Steam API key configured. Tell whoever runs this bot to fix it.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        steam_id = await resolve_steam_id(self.session, steam_id_or_vanity)
        if not steam_id:
            await interaction.followup.send("Couldn't resolve that. Check the ID/vanity URL and try again.")
            return

        await db.update_settings(interaction.user.id, steam_id=steam_id)
        await interaction.followup.send(f"Linked. SteamID64: {steam_id}")

    @steam_group.command(name="show", description="Show a linked Steam profile's current/last-played game")
    @app_commands.describe(member="Whose Steam info to show (defaults to you)")
    async def show(self, interaction: discord.Interaction, member: discord.Member | None = None):
        if not STEAM_API_KEY:
            await interaction.response.send_message("No Steam API key configured.", ephemeral=True)
            return

        target = member or interaction.user
        row = await db.get_user(target.id)
        if not row or not row.get("steam_id"):
            await interaction.response.send_message(f"{target.display_name} hasn't linked Steam. Gonk.")
            return

        await interaction.response.defer()
        url = f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v2/"
        params = {"key": STEAM_API_KEY, "steamids": row["steam_id"]}
        async with self.session.get(url, params=params) as resp:
            if resp.status != 200:
                await interaction.followup.send("Steam didn't answer. Try later.")
                return
            data = await resp.json()

        players = data.get("response", {}).get("players", [])
        if not players:
            await interaction.followup.send("Steam gave me nothing. Try again later.")
            return

        p = players[0]
        name = p.get("personaname", "Unknown")
        game = p.get("gameextrainfo")
        status = f"Currently playing **{game}**." if game else "Not currently in-game."
        await interaction.followup.send(f"**{name}**\n{status}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SteamCog(bot))
