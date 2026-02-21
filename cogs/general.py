import discord
from discord.ext import commands


class General(commands.Cog):
    """General-purpose commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ping", description="Check bot latency.")
    async def ping(self, ctx: commands.Context):
        latency_ms = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! Latency: **{latency_ms} ms**")

    @commands.hybrid_command(name="info", description="Show information about the bot.")
    async def info(self, ctx: commands.Context):
        embed = discord.Embed(
            title="ARC Uplink Bot",
            description=(
                "ARC Uplink Bot is a relay and notification bot that keeps your "
                "server informed with the latest updates and announcements."
            ),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(name="Prefix", value="`!`", inline=True)
        embed.add_field(name="Latency", value=f"{round(self.bot.latency * 1000)} ms", inline=True)
        embed.set_footer(text="ARC Uplink Bot • MIT License")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
