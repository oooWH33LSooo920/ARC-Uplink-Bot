"""ARC Uplink – Discord bot for ARC Raiders communities."""

import asyncio
import json
import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "data", "guild_settings.json")
COGS = [
    "cogs.trials",
    "cogs.events",
    "cogs.expeditions",
    "cogs.quests",
]


def _load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except Exception as exc:
        logger.warning("Could not load guild settings: %s", exc)
        return {}


def _save_settings(settings: dict) -> None:
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as fh:
        json.dump(settings, fh, indent=2)


class ArcUplinkBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.guild_settings: dict = _load_settings()

    def save_settings(self) -> None:
        _save_settings(self.guild_settings)

    async def setup_hook(self) -> None:
        for cog in COGS:
            try:
                await self.load_extension(cog)
                logger.info("Loaded cog: %s", cog)
            except Exception as exc:
                logger.error("Failed to load cog %s: %s", cog, exc)
        await self.tree.sync()
        logger.info("Slash commands synced.")

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)  # type: ignore[union-attr]
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="ARC Raiders | /trials /liveevents",
            )
        )


async def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN environment variable is not set. "
            "Copy .env.example to .env and fill in your bot token."
        )

    async with ArcUplinkBot() as bot:
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
