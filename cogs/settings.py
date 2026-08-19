import discord
from discord import app_commands
from discord.ext import commands

import db


def format_settings(row: dict | None) -> str:
    if not row or all(row.get(k) is None for k in ("dpi", "sens", "resolution", "crosshair")):
        return "No settings on file. Gonk didn't even bother setting anything up."

    lines = []
    dpi = row.get("dpi")
    sens = row.get("sens")
    if dpi is not None:
        lines.append(f"DPI: {dpi}")
    if sens is not None:
        lines.append(f"Sens: {sens}")
    if dpi is not None and sens is not None:
        lines.append(f"eDPI: {dpi * sens:.0f}")
    if row.get("resolution"):
        lines.append(f"Resolution: {row['resolution']}")
    if row.get("crosshair"):
        lines.append(f"Crosshair: {row['crosshair']}")
    return "\n".join(lines)


class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    settings_group = app_commands.Group(name="settings", description="View or update your CS2 settings")

    @settings_group.command(name="set", description="Update your CS2 settings")
    @app_commands.describe(
        dpi="Mouse DPI",
        sens="In-game sensitivity",
        resolution="e.g. 1920x1080",
        crosshair="Crosshair share code or description",
    )
    async def set_settings(
        self,
        interaction: discord.Interaction,
        dpi: int | None = None,
        sens: float | None = None,
        resolution: str | None = None,
        crosshair: str | None = None,
    ):
        if all(v is None for v in (dpi, sens, resolution, crosshair)):
            await interaction.response.send_message(
                "You gave me nothing to update. Gonk move.", ephemeral=True
            )
            return

        await db.update_settings(
            interaction.user.id, dpi=dpi, sens=sens, resolution=resolution, crosshair=crosshair
        )
        await interaction.response.send_message(
            "Settings updated. Try to remember them yourself next time.", ephemeral=True
        )

    @settings_group.command(name="show", description="Show your or another user's CS2 settings")
    @app_commands.describe(member="Whose settings to show (defaults to you)")
    async def show_settings(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ):
        target = member or interaction.user
        row = await db.get_user(target.id)
        text = format_settings(row)
        header = "Your settings:" if target.id == interaction.user.id else f"{target.display_name}'s settings:"
        await interaction.response.send_message(f"{header}\n{text}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))
