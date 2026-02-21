import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import datetime
import logging

logger = logging.getLogger(__name__)

METAFORGE_BASE = "https://metaforge.app/api/arc-raiders"
TRIALS_RESET_WEEKDAY = 3  # Thursday (0=Monday)
TRIALS_RESET_HOUR = 10    # 10:00 UTC


def _next_reset() -> datetime.datetime:
    """Return the next weekly trials reset as a UTC-aware datetime."""
    now = datetime.datetime.now(datetime.timezone.utc)
    days_ahead = (TRIALS_RESET_WEEKDAY - now.weekday()) % 7
    reset = now.replace(hour=TRIALS_RESET_HOUR, minute=0, second=0, microsecond=0)
    if days_ahead == 0 and now >= reset:
        days_ahead = 7
    reset += datetime.timedelta(days=days_ahead)
    return reset


class Trials(commands.Cog):
    """Weekly Trials commands and auto-post task."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._last_posted_week: int | None = None
        self.weekly_trials_task.start()

    def cog_unload(self) -> None:
        self.weekly_trials_task.cancel()

    # ------------------------------------------------------------------ helpers

    async def _fetch_trials(self, session: aiohttp.ClientSession) -> dict | None:
        """Fetch current weekly trials from MetaForge. Returns None on failure."""
        try:
            async with session.get(
                f"{METAFORGE_BASE}/weekly-trials",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
        except Exception as exc:
            logger.warning("Failed to fetch trials: %s", exc)
        return None

    def _build_trials_embed(self, data: dict) -> discord.Embed:
        """Build a Discord embed from trials API data or a fallback message."""
        embed = discord.Embed(
            title="⚔️ ARC Raiders – Weekly Trials",
            colour=discord.Colour.orange(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if data:
            week = data.get("week", "?")
            period = data.get("period", {})
            start = period.get("from", "")
            end = period.get("to", "")
            if start and end:
                embed.add_field(
                    name="📅 Period",
                    value=f"{start} → {end}",
                    inline=False,
                )
            objectives = data.get("objectives", [])
            if objectives:
                embed.add_field(
                    name="🎯 Objectives",
                    value="\n".join(f"• {o}" for o in objectives),
                    inline=False,
                )
            embed.set_footer(text=f"Season Week {week} · ARC Uplink")
        else:
            embed.description = (
                "Weekly trials data is currently unavailable. "
                "Check https://metaforge.app/arc-raiders/weekly-trials for the latest info."
            )
            embed.set_footer(text="ARC Uplink")

        next_reset = _next_reset()
        embed.add_field(
            name="🔄 Next Reset",
            value=discord.utils.format_dt(next_reset, style="R"),
            inline=False,
        )
        return embed

    async def _post_to_channels(self, embed: discord.Embed) -> None:
        """Post the trials embed to all configured guild channels."""
        guild_settings: dict = self.bot.guild_settings  # type: ignore[attr-defined]
        for guild_id, settings in guild_settings.items():
            channel_id = settings.get("trials_channel")
            if not channel_id:
                continue
            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                continue
            try:
                await channel.send(embed=embed)  # type: ignore[union-attr]
            except discord.HTTPException as exc:
                logger.warning("Could not post trials to guild %s: %s", guild_id, exc)

    # ------------------------------------------------------------------ tasks

    @tasks.loop(minutes=5)
    async def weekly_trials_task(self) -> None:
        """Check once every 5 minutes whether the week has rolled over."""
        now = datetime.datetime.now(datetime.timezone.utc)
        current_week = now.isocalendar().week
        if current_week == self._last_posted_week:
            return

        async with aiohttp.ClientSession() as session:
            data = await self._fetch_trials(session)

        embed = self._build_trials_embed(data or {})
        await self._post_to_channels(embed)
        self._last_posted_week = current_week

    @weekly_trials_task.before_loop
    async def _before_trials_task(self) -> None:
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ commands

    @app_commands.command(
        name="trials",
        description="Show the current week's ARC Raiders weekly trials.",
    )
    async def trials(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            data = await self._fetch_trials(session)
        embed = self._build_trials_embed(data or {})
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="setweeklytrials",
        description="Set the channel where weekly trial updates are posted automatically.",
    )
    @app_commands.describe(channel="The text channel to post weekly trial updates in.")
    @app_commands.default_permissions(administrator=True)
    async def setweeklytrials(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild_settings: dict = self.bot.guild_settings  # type: ignore[attr-defined]
        gid = str(interaction.guild_id)
        guild_settings.setdefault(gid, {})["trials_channel"] = str(channel.id)
        self.bot.save_settings()  # type: ignore[attr-defined]
        await interaction.response.send_message(
            f"✅ Weekly trials will now be posted in {channel.mention}.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Trials(bot))
