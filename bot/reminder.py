"""Reminder configuration and scheduling."""

import re
from datetime import datetime
from typing import Callable

from . import dates, storage

__all__ = [
    "set_dates_reminder_time",
    "get_dates_reminder_time",
    "set_dates_reminder_channel",
    "set_dates_reminder_message",
    "format_dates_reminder_message",
    "get_dates_reminder_channel",
    "get_dates_reminder_message",
    "get_due_date_reminders",
]

_time_re = re.compile(r"^(\d{2}):(\d{2})$")
reminder_hour: int = 18
reminder_minute: int = 0
reminder_channel_id: str | None = None
reminder_message_template: str = "Rappel raid: la date {date} est aujourd'hui."


def _load_reminder_config() -> None:
    """Load reminder config from disk."""
    global reminder_hour, reminder_minute, reminder_channel_id, reminder_message_template
    data = storage.load_data()
    if data and data.get("reminder"):
        cfg = data["reminder"]
        if isinstance(cfg.get("time"), str):
            m = _time_re.match(cfg["time"].strip())
            if m:
                reminder_hour = int(m.group(1))
                reminder_minute = int(m.group(2))
        if isinstance(cfg.get("channelId"), str):
            reminder_channel_id = cfg["channelId"]
        if isinstance(cfg.get("message"), str):
            reminder_message_template = cfg["message"]


def _save_reminder_config() -> None:
    """Save reminder config to disk."""
    data = storage.load_data()
    data["dates"] = data.get("dates", []) if isinstance(data.get("dates"), list) else (data.get("dates", []) if data.get("dates") else [])
    data["reminder"] = {
        "time": f"{str(reminder_hour).zfill(2)}:{str(reminder_minute).zfill(2)}",
        "channelId": reminder_channel_id,
        "message": reminder_message_template,
    }
    storage.save_data(data)


# Initialize from disk
_load_reminder_config()


def set_dates_reminder_time(time_input: str) -> str:
    """Set the reminder time in HH:mm format."""
    if not isinstance(time_input, str):
        raise ValueError("Reminder time must be a string in HH:mm format")

    match = _time_re.match(time_input.strip())
    if not match:
        raise ValueError("Reminder time must be in HH:mm format")

    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        raise ValueError("Reminder time must be a valid 24h time (HH:mm)")

    global reminder_hour, reminder_minute
    reminder_hour, reminder_minute = hour, minute
    _save_reminder_config()
    return get_dates_reminder_time()


def get_dates_reminder_time() -> str:
    """Get the current reminder time."""
    return f"{str(reminder_hour).zfill(2)}:{str(reminder_minute).zfill(2)}"


def set_dates_reminder_channel(channel_id: str | None) -> str | None:
    """Set the reminder channel ID."""
    if channel_id is not None:
        if not isinstance(channel_id, str) or not channel_id.isdigit():
            raise ValueError("Reminder channel must be a valid Discord channel id")

    global reminder_channel_id
    reminder_channel_id = channel_id
    _save_reminder_config()
    return reminder_channel_id


def set_dates_reminder_message(message_input: str) -> str:
    """Set the reminder message template."""
    if not isinstance(message_input, str):
        raise ValueError("Reminder message must be a string")

    trimmed = message_input.strip()
    if not trimmed:
        raise ValueError("Reminder message cannot be empty")
    if len(trimmed) > 2000:
        raise ValueError("Reminder message cannot exceed 2000 characters")

    global reminder_message_template
    reminder_message_template = trimmed
    _save_reminder_config()
    return reminder_message_template


def format_dates_reminder_message(date: str) -> str:
    """Format the reminder message with the given date."""
    return reminder_message_template.replace("{date}", date)


def get_due_date_reminders(has_date: Callable[[str], bool], now: datetime | None = None) -> list[dict]:
    """Get reminders that are due right now."""
    if not callable(has_date):
        raise TypeError("hasDate must be a callable")

    now = now or datetime.now()
    current_hour, current_minute = now.hour, now.minute

    if current_hour != reminder_hour or current_minute != reminder_minute:
        return []

    today_str = dates.get_today_date_string(now)
    if not has_date(today_str):
        return []

    if not reminder_channel_id:
        return []

    return [{"date": today_str, "channelId": reminder_channel_id}]


def get_dates_reminder_channel() -> str | None:
    """Get the configured reminder channel."""
    return reminder_channel_id


def get_dates_reminder_message() -> str:
    """Get the configured reminder message."""
    return reminder_message_template
