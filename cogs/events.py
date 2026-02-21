import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import datetime
import logging

logger = logging.getLogger(__name__)

METAFORGE_BASE = "https://metaforge.app/api/arc-raiders"
CHECK_INTERVAL_MINUTES = 10


class Events(commands.Cog):
    """Live events commands and auto-notification task."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._known_event_ids: set[str] = set()
        self.live_events_task.start()

    def cog_unload(self) -> None:
        self.live_events_task.cancel()

    # ------------------------------------------------------------------ helpers

    async def _fetch_events(self, session: aiohttp.ClientSession) -> list[dict]:
        """Fetch active live events from MetaForge. Returns an empty list on failure."""
        try:
            async with session.get(
                f"{METAFORGE_BASE}/events",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    return payload.get("data", payload) if isinstance(payload, dict) else payload
        except Exception as exc:
            logger.warning("Failed to fetch live events: %s", exc)
        return []

    def _build_events_embed(self, events: list[dict]) -> discord.Embed:
        """Build a Discord embed for the current live events."""
        embed = discord.Embed(
            title="📡 ARC Raiders – Live Events",
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if events:
            for event in events:
                name = event.get("name") or event.get("title") or "Unnamed Event"
                desc = event.get("description") or ""
                ends = event.get("ends_at") or event.get("end_date") or ""
                value = desc
                if ends:
                    try:
                        dt = datetime.datetime.fromisoformat(ends.replace("Z", "+00:00"))
                        value += f"\n⏰ Ends {discord.utils.format_dt(dt, style='R')}"
                    except ValueError:
                        value += f"\n⏰ Ends: {ends}"
                embed.add_field(name=f"🔴 {name}", value=value or "No details available.", inline=False)
        else:
            embed.description = (
                "No live events are currently active.\n"
                "Check https://metaforge.app/arc-raiders for the latest updates."
            )
        embed.set_footer(text="ARC Uplink")
        return embed

    async def _post_new_events(self, new_events: list[dict]) -> None:
        """Post newly discovered events to all configured guild channels."""
        guild_settings: dict = self.bot.guild_settings  # type: ignore[attr-defined]
        for guild_id, settings in guild_settings.items():
            channel_id = settings.get("events_channel")
            if not channel_id:
                continue
            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                continue
            for event in new_events:
                embed = self._build_events_embed([event])
                embed.title = "📡 New Live Event Detected!"
                try:
                    await channel.send(embed=embed)  # type: ignore[union-attr]
                except discord.HTTPException as exc:
                    logger.warning("Could not post event to guild %s: %s", guild_id, exc)

    # ------------------------------------------------------------------ tasks

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def live_events_task(self) -> None:
        """Periodically check for new live events and notify configured channels."""
        async with aiohttp.ClientSession() as session:
            events = await self._fetch_events(session)

        new_events = []
        for event in events:
            event_id = str(event.get("id") or event.get("name") or "")
            if event_id and event_id not in self._known_event_ids:
                self._known_event_ids.add(event_id)
                new_events.append(event)

        if new_events:
            await self._post_new_events(new_events)

    @live_events_task.before_loop
    async def _before_events_task(self) -> None:
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------ commands

    @app_commands.command(
        name="liveevents",
        description="Show currently active ARC Raiders live events.",
    )
    async def liveevents(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            events = await self._fetch_events(session)
        embed = self._build_events_embed(events)
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="setliveevents",
        description="Set the channel where live event notifications are posted automatically.",
    )
    @app_commands.describe(channel="The text channel to post live event alerts in.")
    @app_commands.default_permissions(administrator=True)
    async def setliveevents(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ) -> None:
        guild_settings: dict = self.bot.guild_settings  # type: ignore[attr-defined]
        gid = str(interaction.guild_id)
        guild_settings.setdefault(gid, {})["events_channel"] = str(channel.id)
        self.bot.save_settings()  # type: ignore[attr-defined]
        await interaction.response.send_message(
            f"✅ Live event alerts will now be posted in {channel.mention}.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Events(bot))
