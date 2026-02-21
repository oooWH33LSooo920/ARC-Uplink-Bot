import collections
import logging
import os

import aiohttp
import discord
from discord.ext import commands, tasks

logger = logging.getLogger("ARC-Uplink.uplink")

UPLINK_CHANNEL_ID = int(os.getenv("UPLINK_CHANNEL_ID", "0"))
UPLINK_FEED_URL = os.getenv("UPLINK_FEED_URL", "")


class Uplink(commands.Cog):
    """Uplink cog — relays updates from a configured feed URL to a Discord channel."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._seen_entries: collections.deque[str] = collections.deque(maxlen=1000)
        if UPLINK_CHANNEL_ID and UPLINK_FEED_URL:
            self.poll_feed.start()

    def cog_unload(self):
        self.poll_feed.cancel()

    @tasks.loop(minutes=5)
    async def poll_feed(self):
        """Periodically fetches the uplink feed and posts new entries."""
        channel = self.bot.get_channel(UPLINK_CHANNEL_ID)
        if channel is None:
            logger.warning("Uplink channel %s not found.", UPLINK_CHANNEL_ID)
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(UPLINK_FEED_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        logger.warning("Feed returned HTTP %s", resp.status)
                        return
                    data = await resp.json()
        except Exception as exc:
            logger.error("Error fetching uplink feed: %s", exc)
            return

        entries = data if isinstance(data, list) else data.get("entries", [])
        for entry in entries:
            entry_id = str(entry.get("id", ""))
            if not entry_id or entry_id in self._seen_entries:
                continue
            self._seen_entries.append(entry_id)
            title = entry.get("title", "New Update")
            url = entry.get("url", "")
            description = entry.get("description", "")
            embed = discord.Embed(
                title=title,
                url=url if url else None,
                description=description,
                colour=discord.Colour.green(),
            )
            embed.set_footer(text="ARC Uplink")
            await channel.send(embed=embed)

    @poll_feed.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="uplink", description="Show the current uplink feed URL.")
    @commands.has_permissions(manage_guild=True)
    async def uplink_info(self, ctx: commands.Context):
        if not UPLINK_FEED_URL:
            await ctx.send("No uplink feed is configured. Set `UPLINK_FEED_URL` in your `.env`.")
        else:
            await ctx.send(f"🔗 Uplink feed: `{UPLINK_FEED_URL}`  |  Channel: <#{UPLINK_CHANNEL_ID}>")


async def setup(bot: commands.Bot):
    await bot.add_cog(Uplink(bot))
