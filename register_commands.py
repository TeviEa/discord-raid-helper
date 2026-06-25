"""Register slash commands with Discord (Python)."""

import asyncio
import os

from bot.discord_api import install_global_commands
from bot.commands import ALL_COMMANDS

APP_ID = os.environ.get("APP_ID")

if not APP_ID:
    print("ERROR: APP_ID not set in environment")
    exit(1)


async def main():
    await install_global_commands(APP_ID, ALL_COMMANDS)
    print("Slash commands registered successfully")


if __name__ == "__main__":
    asyncio.run(main())
