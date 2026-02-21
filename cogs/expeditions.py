import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import json
import os
import datetime
import logging

logger = logging.getLogger(__name__)

METAFORGE_BASE = "https://metaforge.app/api/arc-raiders"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "expeditions.json")
CHECK_INTERVAL_HOURS = 6


def _load_local_expeditions() -> list[dict]:
    try:
        with open(DATA_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.warning("Could not load local expeditions: %s", exc)
        return []


class Expeditions(commands.Cog):
    """Expedition commands and auto-post task."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._last_expedition_id: str | None = None
        self.expedition_task.start()

    def cog_unload(self) -> None:
        self.expedition_task.cancel()

    # ------------------------------------------------------------------ helpers

    async def _fetch_expeditions(self, session: aiohttp.ClientSession) -> list[dict]:
        """Fetch expedition data from MetaForge. Falls back to local data."""
        try:
            async with session.get(
                f"{METAFORGE_BASE}/arcs",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    return payload.get("data", payload) if isinstance(payload, dict) else payload
        except Exception as exc:
            logger.warning("Failed to fetch expeditions from API: %s", exc)
        return _load_local_expeditions()

    def _build_expedition_embed(self, expedition: dict) -> discord.Embed:
        """Build a Discord embed for a single expedition."""
        embed = discord.Embed(
            title=f"🗺️ Expedition: {expedition.get('name', 'Unknown')}",
            description=expedition.get("description", ""),
            colour=discord.Colour.teal(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        objectives = expedition.get("objectives") or []
        if objectives:
            embed.add_field(
                name="🎯 Objectives",
                value="\n".join(f"• {o}" for o in objectives),
                inline=False,
            )
        difficulty = expedition.get("difficulty") or expedition.get("risk")
        if difficulty:
            embed.add_field(name="⚠️ Difficulty", value=difficulty, inline=True)

        recommended = expedition.get("recommended_players") or expedition.get("recommended")
        if recommended:
            embed.add_field(name="👥 Recommended Players", value=str(recommended), inline=True)

        rewards = expedition.get("rewards") or []
        if rewards:
            embed.add_field(
                name="🏆 Rewards",
                value="\n".join(f"• {r}" for r in rewards),
                inline=False,
            )
        embed.set_footer(text="ARC Uplink")
        return embed

    def _build_expedition_list_embed(self, expeditions: list[dict]) -> discord.Embed:
        """Build an embed listing all available expeditions."""
        embed = discord.Embed(
            title="🗺️ ARC Raiders – Available Expeditions",
            colour=discord.Colour.teal(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if expeditions:
            for exp in expeditions:
                difficulty = exp.get("difficulty") or exp.get("risk") or "Unknown"
                embed.add_field(
                    name=exp.get("name", "Unknown"),
                    value=f"Difficulty: **{difficulty}**",
                    inline=True,
                )
        else:
            embed.description = (
                "No expedition data is currently available.\n"
                "Check https://metaforge.app/arc-raiders for the latest information."
            )
        embed.set_footer(text="ARC Uplink")
        return embed

    async def _post_to_channels(self, embed: discord.Embed) -> None:
        guild_settings: dict = self.bot.guild_settings  # type: ignore[attr-defined]
        for guild_id, settings in guild_settings.items():
            channel_id = settings.get("expedition_channel")
            if not channel_id:
                continue
            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                continue
            try:
                await channel.send(embed=embed)  # type: ignore[union-attr]
            except discord.HTTPException as exc:
                logger.warning("Could not post expedition to guild %s: %s", guild_id, exc)

    # ------------------------------------------------------------------ tasks

    @tasks.loop(hours=CHECK_INTERVAL_HOURS)
    async def expedition_task(self) -> None:
        """Periodically check for new expeditions and notify configured channels."""
        async with aiohttp.ClientSession() as session:
            expeditions = await self._fetch_expeditions(session)

        if not expeditions:
            return

        latest = expeditions[0]
        latest_id = str(latest.get("id") or latest.get("name") or "")
        if latest_id and latest_id == self._last_expedition_id:
            return

        self._last_expedition_id = latest_id
        embed = self._build_expedition_embed(latest)
        embed.title = f"🗺️ New Expedition Available: {latest.get('name', 'Unknown')}"
        await self._post_to_channels(embed)

    @expedition_task.before_loop
    async def _before_expedition_task(self) -> None:
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ commands

    @app_commands.command(
        name="expedition",
        description="Show the latest available ARC Raiders expedition.",
    )
    async def expedition(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            expeditions = await self._fetch_expeditions(session)
        if expeditions:
            embed = self._build_expedition_embed(expeditions[0])
        else:
            embed = self._build_expedition_list_embed([])
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="expeditions",
        description="List all available ARC Raiders expeditions.",
    )
    async def expeditions(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            data = await self._fetch_expeditions(session)
        embed = self._build_expedition_list_embed(data)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="setexpedition",
        description="Set the channel where expedition update notifications are posted automatically.",
    )
    @app_commands.describe(channel="The text channel to post expedition alerts in.")
    @app_commands.default_permissions(administrator=True)
    async def setexpedition(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild_settings: dict = self.bot.guild_settings  # type: ignore[attr-defined]
        gid = str(interaction.guild_id)
        guild_settings.setdefault(gid, {})["expedition_channel"] = str(channel.id)
        self.bot.save_settings()  # type: ignore[attr-defined]
        await interaction.response.send_message(
            f"✅ Expedition updates will now be posted in {channel.mention}.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Expeditions(bot))
