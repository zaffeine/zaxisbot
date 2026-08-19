import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

import db

CS2_APP_ID = 730
CS2_CONTEXT_ID = 2


class InventoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    @app_commands.command(name="inventory", description="Show a summary of a linked CS2 inventory")
    @app_commands.describe(member="Whose inventory to show (defaults to you)")
    async def inventory(self, interaction: discord.Interaction, member: discord.Member | None = None):
        target = member or interaction.user
        row = await db.get_user(target.id)
        if not row or not row.get("steam_id"):
            await interaction.response.send_message(
                f"{target.display_name} hasn't linked Steam. No inventory to gonk through."
            )
            return

        await interaction.response.defer()
        steam_id = row["steam_id"]
        url = f"https://steamcommunity.com/inventory/{steam_id}/{CS2_APP_ID}/{CS2_CONTEXT_ID}"
        params = {"l": "english", "count": 100}

        async with self.session.get(url, params=params) as resp:
            if resp.status == 403:
                await interaction.followup.send("Inventory is private. Can't see gonk.")
                return
            if resp.status != 200:
                await interaction.followup.send(f"Steam said no ({resp.status}). Try later.")
                return
            data = await resp.json(content_type=None)

        descriptions = data.get("descriptions", []) if data else []
        total_items = (data or {}).get("total_inventory_count", len(descriptions))
        names = [
            d.get("market_hash_name") or d.get("name")
            for d in descriptions
            if d.get("marketable")
        ]
        preview = ", ".join(names[:5]) if names else "nothing marketable"

        await interaction.followup.send(
            f"**{target.display_name}'s CS2 inventory**\nTotal items: {total_items}\nSample: {preview}"
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(InventoryCog(bot))
