"""Discord REST API client."""

import json
import os

import aiohttp

__all__ = ["discord_request", "install_global_commands"]

BASE_URL = "https://discord.com/api/v10"
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")
USER_AGENT = "DiscordBot (https://github.com/discord/discord-example-app, 1.0.0)"


async def discord_request(endpoint: str, method: str = "GET", body: dict | None = None) -> aiohttp.ClientResponse:
    """Make a request to the Discord API."""
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": USER_AGENT,
    }

    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, json=body) as resp:
            if resp.status >= 400:
                data = await resp.json()
                print(f"[{__name__}] Discord API error: {resp.status}")
                raise Exception(json.dumps(data))
            return resp


async def install_global_commands(app_id: str, commands: list[dict]) -> None:
    """Register slash commands with Discord."""
    endpoint = f"applications/{app_id}/commands"
    try:
        await discord_request(endpoint, method="PUT", body=commands)
    except Exception as e:
        print(f"[{__name__}] Failed to install commands: {e}")
