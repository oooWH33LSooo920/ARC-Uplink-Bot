import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import json
import os
import datetime
import logging

logger = logging.getLogger(__name__)

METAFORGE_BASE = "https://metaforge.app/api/arc-raiders"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "quests.json")
MAX_QUEST_LIST_DISPLAY = 15


def _load_local_quests() -> list[dict]:
    try:
        with open(DATA_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.warning("Could not load local quests: %s", exc)
        return []


class Quests(commands.Cog):
    """Quest lookup commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------ helpers

    async def _fetch_quests(self, session: aiohttp.ClientSession) -> list[dict]:
        """Fetch quest data from MetaForge. Falls back to local data."""
        try:
            async with session.get(
                f"{METAFORGE_BASE}/quests",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    payload = await resp.json()
                    return payload.get("data", payload) if isinstance(payload, dict) else payload
        except Exception as exc:
            logger.warning("Failed to fetch quests from API: %s", exc)
        return _load_local_quests()

    def _find_quest(self, quests: list[dict], name: str) -> dict | None:
        """Case-insensitive quest lookup by name."""
        name_lower = name.lower()
        for quest in quests:
            qname = quest.get("name") or quest.get("title") or ""
            if name_lower in qname.lower():
                return quest
        return None

    def _build_quest_embed(self, quest: dict) -> discord.Embed:
        """Build a Discord embed for a single quest."""
        embed = discord.Embed(
            title=f"📋 Quest: {quest.get('name') or quest.get('title', 'Unknown')}",
            description=quest.get("description") or quest.get("summary") or "",
            colour=discord.Colour.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        objectives = quest.get("objectives") or []
        if objectives:
            embed.add_field(
                name="🎯 Objectives",
                value="\n".join(f"• {o}" for o in objectives),
                inline=False,
            )
        difficulty = quest.get("difficulty") or quest.get("risk")
        if difficulty:
            embed.add_field(name="⚠️ Difficulty", value=difficulty, inline=True)

        rewards = quest.get("rewards") or []
        if rewards:
            embed.add_field(
                name="🏆 Rewards",
                value="\n".join(f"• {r}" for r in rewards),
                inline=False,
            )
        embed.set_footer(text="ARC Uplink")
        return embed

    def _build_quest_list_embed(self, quests: list[dict]) -> discord.Embed:
        """Build an embed listing available quests."""
        embed = discord.Embed(
            title="📋 ARC Raiders – Available Quests",
            colour=discord.Colour.blue(),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        if quests:
            displayed = quests[:MAX_QUEST_LIST_DISPLAY]
            lines = []
            for quest in displayed:
                name = quest.get("name") or quest.get("title") or "Unknown"
                difficulty = quest.get("difficulty") or quest.get("risk") or "?"
                lines.append(f"• **{name}** – {difficulty}")
            embed.description = "\n".join(lines)
            if len(quests) > MAX_QUEST_LIST_DISPLAY:
                embed.set_footer(
                    text=f"Showing {MAX_QUEST_LIST_DISPLAY} of {len(quests)} quests · ARC Uplink"
                )
            else:
                embed.set_footer(text="ARC Uplink")
        else:
            embed.description = (
                "No quest data is currently available.\n"
                "Check https://metaforge.app/arc-raiders for the latest information."
            )
            embed.set_footer(text="ARC Uplink")
        return embed

    # ------------------------------------------------------------------ commands

    @app_commands.command(
        name="quest",
        description="Look up an ARC Raiders quest by name.",
    )
    @app_commands.describe(name="Part of the quest name to search for.")
    async def quest(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            quests = await self._fetch_quests(session)
        result = self._find_quest(quests, name)
        if result:
            await interaction.followup.send(embed=self._build_quest_embed(result))
        else:
            await interaction.followup.send(
                f"❌ No quest found matching **{discord.utils.escape_markdown(name)}**. "
                "Use `/quest_list` to see all available quests.",
                ephemeral=True,
            )

    @app_commands.command(
        name="quest_list",
        description="List all available ARC Raiders quests.",
    )
    async def quest_list(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            quests = await self._fetch_quests(session)
        await interaction.followup.send(embed=self._build_quest_list_embed(quests))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quests(bot))
