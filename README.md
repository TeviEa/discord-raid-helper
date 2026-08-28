# Discord Raid Helper — Python Bot

A Discord bot for managing raid dates, sending scheduled reminders, and running weekly availability polls.

## Prerequisites

- Python 3.12+
- A Discord bot token and app ID
- Docker (optional, for production deployment)

## Setup

### 1. Get Discord credentials

Fetch the credentials from your [Discord app settings](https://discord.com/developers/applications) and add them to a `.env` file:

```env
APP_ID=your_app_id
DISCORD_TOKEN=your_bot_token
PUBLIC_KEY=your_public_key
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Register slash commands

```bash
python register_commands.py
```

This registers all slash commands with Discord.

### 4. Create configuration files

The bot uses a **hybrid configuration** system: static settings in `config.json` (requires restart to change) and dynamic state in `state.json` (updated live via Discord commands).

Create the data directory and both files:

```bash
mkdir -p .data
```

**`.data/config.json`** — Static configuration (edit manually, restart bot to apply):

```json
{
  "raid": {
    "days": ["tuesday", "thursday"]
  },
  "reminder": {
    "time": "10:00"
  },
  "poll": {
    "message": "Session bonus ?",
    "durationHours": 48,
    "sendHour": 21,
    "sendMinute": 0
  },
  "calendar": {
    "title": "🔔 Prochaines sessions 🔔",
    "color": 3900150
  }
}
```

| Key | Description |
|-----|-------------|
| `raid.days` | Weekdays that are raid days (excluded from poll options) |
| `reminder.time` | Time to send raid reminders (HH:mm, 24h format) |
| `poll.message` | Default poll question text |
| `poll.durationHours` | How long the poll stays open (1–1008) |
| `poll.sendHour` | Hour to send the poll (0–23) |
| `poll.sendMinute` | Minute to send the poll (0–59) |
| `calendar.title` | Title of the calendar embed |
| `calendar.color` | Embed color as decimal integer (0–0xFFFFFF) |

**`data/state.json`** — Dynamic state (updated automatically by Discord commands):

```json
{
  "dates": ["27/08/26", "01/09/26", "03/09/26"],
  "reminder": {
    "channelId": "1322266736182952018",
    "message": "🔔 Rappel 🔔 <@&1473624914375344160> on raid ce soir !!"
  },
  "calendar": {
    "channelId": "1534198461094690857",
    "messageId": "1234567890123456789"
  },
  "poll": {
    "day": "wednesday",
    "channelId": "1503681409511067780",
    "pingRoleId": "1541927314189713459",
    "pauseEnabled": false,
    "pauseUntil": ""
  }
}
```

| Key | Description |
|-----|-------------|
| `dates` | List of upcoming raid dates (dd/mm/yy) |
| `reminder.channelId` | Channel to send reminders to |
| `reminder.message` | Reminder message template (`{date}` placeholder) |
| `calendar.channelId` | Channel to post the calendar embed |
| `poll.day` | Day of the week for the weekly poll |
| `poll.channelId` | Channel to post the poll |
| `poll.pingRoleId` | Role to ping after poll submission |
| `poll.pauseEnabled` | Whether the poll is currently paused |
| `poll.pauseUntil` | Date when pause ends (dd/mm/yy) or empty |

### 5. Run the bot

```bash
python -m bot.server
```

The bot listens on port `3333` by default.

## Docker Deployment

```bash
docker buildx build --platform linux/arm/v7 -t discord-raid-helper .
docker run -d \
  --name discord-raid-helper \
  --restart always \
  -p 127.0.0.1:3333:3333 \
  -v raid-data:/app/data \
  --env-file .env \
  discord-raid-helper
```

### Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ID` | Discord application ID | — |
| `DISCORD_TOKEN` | Discord bot token | — |
| `PUBLIC_KEY` | Discord public key for signature verification | — |
| `DATA_DIR` | Path to the data directory | `/app/data` |
| `PORT` | HTTP port | `3333` |

## Commands

### `/dates` — Raid date management

- `/dates list` — Show upcoming raid dates
- `/dates add dates: 15/05/26,22/05/26` — Add raid dates (comma, space, or semicolon separated)
- `/dates delete dates: 15/05/26` — Delete raid dates
- `/dates max max: 10` — Set maximum number of dates to display

### `/reminder` — Reminder configuration

- `/reminder show` — Show current reminder configuration
- `/reminder channel channel: 1322266736182952018` — Set reminder channel
- `/reminder message message: Rappel raid aujourd'hui ({date})` — Set reminder message template

> ⚠️ Reminder **time** is configured in `config.json` and requires a bot restart to change.

### `/calendar` — Calendar embed

- `/calendar channel channel: 1534198461094690857` — Set channel for the calendar embed (posts it automatically)
- `/calendar delete` — Delete the current calendar message

> ⚠️ Calendar **title** and **color** are configured in `config.json` and require a bot restart to change.

### `/poll` — Weekly availability poll

- `/poll show` — Show current poll configuration
- `/poll day day: wednesday` — Set the day of the weekly poll
- `/poll pause state: on until: 15/09/26` — Pause the poll (until a date or indefinitely)
- `/poll pause state: off` — Resume the poll
- `/poll channel channel: 1503681409511067780` — Set channel for the poll
- `/poll ping role: 1541927314189713459` — Set role to ping after poll submission (leave empty to disable)
- `/poll send` — Send the poll immediately (for testing)

> ⚠️ Poll **message** is configured in `config.json` and requires a bot restart to change.

## Architecture

```
bot/
├── __init__.py      # Package init
├── server.py        # FastAPI server, interaction router, daily check scheduler
├── business.py      # Business logic coordinator (wires dates, reminders, calendar)
├── config.py        # Static config: loads/validates config.json
├── state.py         # Dynamic state: loads/saves state.json
├── dates.py         # Date validation, CRUD, display, sorting
├── reminder.py      # Reminder config and scheduling
├── poll.py          # Weekly availability poll (Discord native polls)
├── calendar.py      # Calendar embed management
├── commands.py      # Slash command definitions
└── discord_api.py   # Discord REST API client (aiohttp)
```

## Development

### Run tests

```bash
python3 -m pytest tests_python/ -v
```

### Run with uvicorn directly

```bash
uvicorn bot.server:_create_app --host 0.0.0.0 --port 3333 --reload
```

## Troubleshooting

### Command registration fails with 429

The bot retries command registration with exponential backoff (2s, 4s, 8s, 16s, max 30s) up to 5 attempts. If it still fails, check:
- Your `APP_ID` and `DISCORD_TOKEN` are correct
- Your bot has the `applications.commands` scope
- You haven't hit Discord's rate limit (wait a few minutes and try again)

### Config values not taking effect

Static values in `config.json` require a bot restart. After editing `config.json`, restart the bot. Dynamic values in `state.json` are updated live via Discord commands.

### Logs not appearing

Check that `uvicorn` log level is set to `info` (default in production). All logs include ISO timestamps.
