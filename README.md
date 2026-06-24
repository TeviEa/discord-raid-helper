# Discord Raid Helper — Python Bot

A Discord bot for managing raid dates and sending scheduled reminders.

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

This registers all slash commands (`/dates`, `/reminder`) with Discord.

### 4. Run the bot

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

### Configuration

- `DATA_DIR` (env): Path to the data directory (default: `/app/data` in Docker)
- `PORT` (env): HTTP port (default: `3333`)

### Data persistence

The bot stores data in `/app/data/values.json`:
```json
{
  "dates": ["01/06/26"],
  "reminder": {
    "time": "18:00",
    "channelId": "1322266736182952018",
    "message": "<@&1473624914375344160> on raid ajd ouaaais"
  }
}
```

## Commands

### `/dates`

- `/dates list` — Show upcoming raid dates
- `/dates add dates: 15/05/26,22/05/26` — Add raid dates (comma, space, or semicolon separated)
- `/dates delete dates: 15/05/26` — Delete raid dates
- `/dates max max: 10` — Set maximum number of dates to display

### `/reminder`

- `/reminder show` — Show current reminder configuration
- `/reminder time time: 18:00` — Set reminder time (HH:mm, 24h format)
- `/reminder channel channel: 1234567890` — Set reminder channel ID
- `/reminder message message: Rappel raid aujourd'hui ({date})` — Set reminder message template

## Development

### Run tests

```bash
python3 -m pytest tests_python/ -v
```

### Run with uvicorn directly

```bash
uvicorn bot.server:_create_app --host 0.0.0.0 --port 3333 --reload
```

## Architecture

```
bot/
├── __init__.py      # Package init
├── server.py        # FastAPI server, interaction router, reminder scheduler
├── business.py      # Business logic coordinator (wires dates, reminders, storage)
├── dates.py         # Date validation, CRUD, display, sorting
├── reminder.py      # Reminder config: time, channel, message template
├── storage.py       # JSON file persistence (atomic writes)
├── commands.py      # Slash command definitions
└── discord_api.py   # Discord REST API client (aiohttp)
```

### Key Design Notes

- **Single source of truth**: `bot/business.py` is the coordinator — all external-facing functions go through it
- **Storage**: JSON file at `/app/data/values.json`, read on startup, written on mutations. Atomic writes via temp-file-then-rename.
- **Timezone**: All dates and times use the machine's local timezone. No hardcoded timezone. All date strings are `DD/MM/YY`.
- **Reminder loop**: Runs every ~3.3s, checks if current local time matches configured reminder time, sends one notification per date per day (debounced via `last_reminder_sent_key`).
- **Autocomplete**: Implemented for `/dates delete dates` — filters existing dates against user input.

## Troubleshooting

### Command registration fails with 429

The bot retries command registration with exponential backoff (2s, 4s, 8s, 16s, max 30s) up to 5 attempts. If it still fails, check:
- Your `APP_ID` and `DISCORD_TOKEN` are correct
- Your bot has the `applications.commands` scope
- You haven't hit Discord's rate limit (wait a few minutes and try again)

### No dates shown after `/dates list`

Ensure the data file exists at `/app/data/values.json` (or your `DATA_DIR` path) and contains:
```json
{
  "dates": ["15/05/26"]
}
```

### Logs not appearing

Check that `uvicorn` log level is set to `info` (default in production). For debug logging, set the `LOG_LEVEL` environment variable.
