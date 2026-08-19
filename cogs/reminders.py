import random

import discord
from discord import app_commands
from discord.ext import commands, tasks

import db
import personality


class RemindersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    reminders_group = app_commands.Group(name="remindme", description="Manage periodic sens-check reminders")

    @reminders_group.command(name="on", description="Enable periodic sens-check reminders via DM")
    @app_commands.describe(interval_hours="How often to check, in hours (default 48)")
    async def enable(self, interaction: discord.Interaction, interval_hours: int = 48):
        if interval_hours <= 0:
            await interaction.response.send_message("Interval has to be a positive number. Gonk.", ephemeral=True)
            return
        await db.set_reminder_state(interaction.user.id, enabled=True, interval_hours=interval_hours)
        await interaction.response.send_message(
            f"Fine. I'll bug you every {interval_hours}h. Don't touch your settings.", ephemeral=True
        )

    @reminders_group.command(name="off", description="Disable sens-check reminders")
    async def disable(self, interaction: discord.Interaction):
        await db.set_reminder_state(interaction.user.id, enabled=False)
        await interaction.response.send_message("Fine, I won't check. Your funeral.", ephemeral=True)

    @tasks.loop(minutes=30)
    async def check_reminders(self):
        due_users = await db.get_due_reminder_users()
        for row in due_users:
            user_id = row["discord_id"]
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(personality.format_sens_question(row))
                await db.mark_reminder_sent(user_id)
            except discord.Forbidden:
                print(f"Could not DM user {user_id} — DMs closed or no shared server.")

    @check_reminders.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if not isinstance(message.channel, discord.DMChannel):
            return

        row = await db.get_user(message.author.id)
        if not row or not row["awaiting_reply"]:
            return

        content = message.content.strip().lower()

        if content == "yes":
            await message.channel.send(random.choice(personality.YES_MESSAGES))
            await db.clear_awaiting(message.author.id)
        elif content == "no":
            await message.channel.send(personality.format_no_reply(row))
            await db.clear_awaiting(message.author.id)
        else:
            streak = await db.increment_invalid_streak(message.author.id)
            ladder = personality.INVALID_ESCALATION
            reply = ladder[streak] if streak < len(ladder) else personality.INVALID_ESCALATION_FINAL
            await message.channel.send(reply)


async def setup(bot: commands.Bot):
    await bot.add_cog(RemindersCog(bot))
