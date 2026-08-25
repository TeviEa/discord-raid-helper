"""Poll feature: weekly raid availability poll using Discord native polls."""

from datetime import datetime, timedelta

__all__ = [
    "set_poll_day",
    "get_poll_day",
    "set_poll_channel",
    "get_poll_channel",
    "set_poll_message",
    "get_poll_message",
    "set_poll_pause",
    "get_poll_pause",
    "set_poll_pause_until",
    "get_poll_pause_until",
    "set_poll_ping_role",
    "get_poll_ping_role",
    "build_poll_message",
    "post_poll_message",
    "poll_config",
]

# --- State ---
_poll_day: str = ""  # e.g. "tuesday"
_poll_channel_id: str | None = None
_poll_message: str = ""
_poll_pause_enabled: bool = False
_poll_pause_until: str = ""  # dd/mm/yy or empty
_poll_ping_role: str | None = None  # Role ID to ping after poll

# Track pending poll task to avoid duplicates
_poll_task = None

# Discord native poll duration in hours (max 1008 = 7 days)
# Change this to adjust how long the poll stays open
_POLL_DURATION_HOURS = 48  # 2 days

# Hour and minute (UTC) when the poll is sent daily
# Change these to adjust when the poll is sent
_POLL_SEND_HOUR = 8
_POLL_SEND_MINUTE = 0

# Day of week mapping (0=Monday, 6=Sunday)
_DAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

_DAY_NAMES_FR = {
    0: "Lundi",
    1: "Mardi",
    2: "Mercredi",
    3: "Jeudi",
    4: "Vendredi",
    5: "Samedi",
    6: "Dimanche",
}

# Emoji for each day of the week (0=Monday, 6=Sunday)
_DAY_EMOJIS = {
    0: "\U0001f4c5",  # 📅 date
    1: "\U0001f4c5",  # 📅 date
    2: "\U0001f4c5",  # 📅 date
    3: "\U0001f4c5",  # 📅 date
    4: "\U0001f4c5",  # 📅 date
    5: "\U0001f4c5",  # 📅 date
    6: "\U0001f4c5",  # 📅 date
}

# Days of the week when raids occur (remove from poll options)
# Format: English day names (monday, tuesday, ..., sunday)
# Change this list to exclude raid days from poll options
RAID_DAYS = ["tuesday", "thursday"]  # Example: raids on Tuesday and Thursday


def set_poll_day(day: str) -> str:
    """Set the poll day of week.

    Args:
        day: Day name in English (monday, tuesday, etc.)

    Returns:
        The new day.

    Raises:
        ValueError: If day is invalid.
    """
    if not isinstance(day, str):
        raise ValueError("Poll day must be a string")

    day_lower = day.strip().lower()
    if day_lower not in _DAY_MAP:
        raise ValueError(f"Invalid day: {day}. Must be one of: {', '.join(_DAY_MAP.keys())}")

    global _poll_day
    _poll_day = day_lower
    _save_poll_config()
    return _poll_day


def get_poll_day() -> str:
    """Get the current poll day."""
    return _poll_day


def set_poll_channel(channel_id: str | None) -> str | None:
    """Set the poll channel ID.

    Args:
        channel_id: Discord channel ID (digits only) or None to disable.

    Returns:
        The new channel ID or None.

    Raises:
        ValueError: If channel_id is not valid.
    """
    if channel_id is not None:
        if not isinstance(channel_id, str) or not channel_id.isdigit():
            raise ValueError("Poll channel must be a valid Discord channel ID (digits only)")

    global _poll_channel_id
    _poll_channel_id = channel_id
    _save_poll_config()
    return _poll_channel_id


def get_poll_channel() -> str | None:
    """Get the current poll channel ID."""
    return _poll_channel_id


def set_poll_message(message: str) -> str:
    """Set the poll question.

    Args:
        message: The poll question (non-empty, max 200 chars for Discord poll).

    Returns:
        The new message.

    Raises:
        ValueError: If message is empty or too long.
    """
    if not isinstance(message, str):
        raise ValueError("Poll message must be a string")

    stripped = message.strip()
    if not stripped:
        raise ValueError("Poll message cannot be empty")
    if len(stripped) > 200:
        raise ValueError("Poll message cannot exceed 200 characters (Discord poll limit)")

    global _poll_message
    _poll_message = stripped
    _save_poll_config()
    return _poll_message


def get_poll_message() -> str:
    """Get the current poll question."""
    return _poll_message


def set_poll_pause(enabled: bool) -> bool:
    """Toggle poll pause.

    Args:
        enabled: True to pause, False to unpause.

    Returns:
        The new enabled state.
    """
    global _poll_pause_enabled
    _poll_pause_enabled = enabled
    _save_poll_config()
    return _poll_pause_enabled


def get_poll_pause() -> bool:
    """Get the current poll pause state."""
    return _poll_pause_enabled


def set_poll_pause_until(until: str) -> str:
    """Set the date when the pause will be lifted.

    Args:
        until: Date string in dd/mm/yy format, or empty to clear.

    Returns:
        The new until date.

    Raises:
        ValueError: If until is not a valid date format.
    """
    if not isinstance(until, str):
        raise ValueError("Poll pause until must be a string (dd/mm/yy or empty)")

    global _poll_pause_until
    if until.strip():
        from . import dates
        if not dates.is_valid_raid_date(until.strip()):
            raise ValueError("Pause until must be a valid date in dd/mm/yy format or empty")
        _poll_pause_until = until.strip()
    else:
        _poll_pause_until = ""
    _save_poll_config()
    return _poll_pause_until


def get_poll_pause_until() -> str:
    """Get the current pause until date."""
    return _poll_pause_until


def set_poll_ping_role(role_id: str | None) -> str | None:
    """Set the Discord role ID to ping after the poll is sent.

    Args:
        role_id: Discord role ID (digits only) or None to disable.

    Returns:
        The new role ID or None.

    Raises:
        ValueError: If role_id is not valid.
    """
    if role_id is not None:
        if not isinstance(role_id, str) or not role_id.isdigit():
            raise ValueError("Poll ping role must be a valid Discord role ID (digits only)")

    global _poll_ping_role
    _poll_ping_role = role_id
    _save_poll_config()
    return _poll_ping_role


def get_poll_ping_role() -> str | None:
    """Get the current poll ping role ID."""
    return _poll_ping_role


def _should_send_poll(now: datetime | None = None) -> bool:
    """Check if the poll should be sent now.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        True if the poll should be sent.
    """
    global _poll_pause_enabled, _poll_pause_until

    now = now or datetime.now()

    # Check pause status
    if _poll_pause_enabled:
        # Check if pause is lifted by date
        if _poll_pause_until:
            from . import dates
            try:
                pause_until_dt = datetime.strptime(_poll_pause_until, "%d/%m/%y")
                if now >= pause_until_dt:
                    # Pause lifted, update state
                    _poll_pause_enabled = False
                    _poll_pause_until = ""
                    _save_poll_config()
            except ValueError:
                pass  # Invalid date, keep paused

        if _poll_pause_enabled:
            return False

    # Check if today is the configured day
    if not _poll_day:
        return False

    day_of_week = now.weekday()  # 0=Monday, 6=Sunday
    target_day = _DAY_MAP.get(_poll_day, -1)
    if day_of_week != target_day:
        return False

    # Check channel is configured
    if not _poll_channel_id:
        return False

    return True


def _get_poll_dates(now: datetime | None = None) -> list[dict]:
    """Get the next 7 dates starting from the configured poll day, excluding RAID_DAYS.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        List of dicts with keys: date_obj, day_name, date_str, day_short
    """
    now = now or datetime.now()

    # Build set of RAID_DAYS weekday numbers for fast lookup
    raid_weekdays = {_DAY_MAP[d] for d in RAID_DAYS if d in _DAY_MAP}

    # Start from the next occurrence of the configured day
    target_day = _DAY_MAP.get(_poll_day, 1)  # Default to tuesday
    days_ahead = (target_day - now.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7  # Next week

    start_date = now + timedelta(days=days_ahead)

    dates = []
    for i in range(7):
        option_date = start_date + timedelta(days=i)
        # Skip dates that fall on RAID_DAYS
        if option_date.weekday() in raid_weekdays:
            continue
        day_name = _DAY_NAMES_FR[option_date.weekday()]
        day_short = day_name[:3]
        date_str = option_date.strftime("%d/%m")
        dates.append({
            "date_obj": option_date,
            "day_name": day_name,
            "date_str": date_str,
            "day_short": day_short,
        })
    return dates


def build_poll_message(now: datetime | None = None) -> dict:
    """Build the Discord native poll message body.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        Discord API message body dict with poll structure.
    """
    dates = _get_poll_dates(now)

    # Build poll answers: 7 days + "Je ne peux pas"
    answers = []
    for d in dates:
        day_emoji = _DAY_EMOJIS[d["date_obj"].weekday()]
        answers.append({
            "poll_media": {
                "text": f"{d['day_short']} {d['date_str']}",
                "emoji": {"name": day_emoji},
            },
        })
    # 8th option: not available
    answers.append({
        "poll_media": {
            "text": "Pas de session bonus",
            "emoji": {"name": "\u274c"},  # ❌
        },
    })

    return {
        "poll": {
            "question": {
                "text": _poll_message,
            },
            "answers": answers,
            "duration": _POLL_DURATION_HOURS,
            "allow_multiselect": True,
            "layout_type": 1,
        },
    }


async def post_poll_message() -> dict | None:
    """Post a Discord native poll in the configured channel, followed by a role ping.

    Returns:
        Dict with 'channel_id' and 'message_id' on success, or None on failure.
    """
    from . import discord_api

    if not _poll_channel_id:
        return None

    try:
        body = build_poll_message()
        data = await discord_api.discord_request(
            f"channels/{_poll_channel_id}/messages",
            method="POST",
            body=body,
            use_form=True,
        )
        _save_poll_config()

        # Post a follow-up message that pings the configured role
        if _poll_ping_role:
            try:
                ping_body = {"content": f"<@&{_poll_ping_role}>"}
                await discord_api.discord_request(
                    f"channels/{_poll_channel_id}/messages",
                    method="POST",
                    body=ping_body,
                )
            except Exception as e:
                print(f"[{__name__}] Failed to post ping message: {e}")

        return {"channel_id": _poll_channel_id, "message_id": data.get("id")}
    except Exception as e:
        print(f"[{__name__}] Failed to post poll message: {e}")
        return None


def _schedule_poll_send() -> None:
    """Schedule a background poll send if one is not already pending."""
    global _poll_task
    if _poll_task is not None and not _poll_task.done():
        return
    import asyncio

    _poll_task = asyncio.create_task(post_poll_message())


def get_poll_config() -> dict:
    """Get the current poll configuration."""
    return {
        "day": _poll_day,
        "channelId": _poll_channel_id,
        "message": _poll_message,
        "pause": {
            "enabled": _poll_pause_enabled,
            "until": _poll_pause_until,
        },
        "pingRole": _poll_ping_role,
    }


def _load_poll_config() -> dict:
    """Load poll configuration from storage."""
    data = storage.load_data()
    return data.get("poll", {})


def _save_poll_config() -> None:
    """Save poll configuration to storage."""
    data = storage.load_data()
    data["poll"] = {
        "day": _poll_day,
        "channelId": _poll_channel_id,
        "message": _poll_message,
        "pause": {
            "enabled": _poll_pause_enabled,
            "until": _poll_pause_until,
        },
        "pingRole": _poll_ping_role,
    }
    storage.save_data(data)


# Import storage at module level
from . import storage

# Initialize from disk
def init_poll() -> None:
    """Initialize poll state from storage."""
    global _poll_day, _poll_channel_id, _poll_message, _poll_pause_enabled, _poll_pause_until, _poll_ping_role

    config = _load_poll_config()
    _poll_day = config.get("day", "")
    _poll_channel_id = config.get("channelId")
    _poll_message = config.get("message", "")
    _poll_pause_enabled = config.get("pause", {}).get("enabled", False)
    _poll_pause_until = config.get("pause", {}).get("until", "")
    _poll_ping_role = config.get("pingRole")
