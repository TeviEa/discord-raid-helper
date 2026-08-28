"""Reminder configuration and scheduling."""

import re
from datetime import datetime
from typing import Callable

from . import config, dates, state

__all__ = [
    "get_dates_reminder_time",
    "set_dates_reminder_channel",
    "set_dates_reminder_message",
    "format_dates_reminder_message",
    "get_dates_reminder_channel",
    "get_dates_reminder_message",
    "get_due_date_reminders",
]

_time_re = re.compile(r"^(\d{2}):(\d{2})$")

# Static config from config.json
_reminder_time = config.get("reminder.time")
reminder_hour: int = int(_reminder_time.split(":")[0])
reminder_minute: int = int(_reminder_time.split(":")[1])

# Dynamic state from state.json
reminder_channel_id: str | None = None
reminder_message_template: str = ""


def _load_reminder_state() -> None:
    """Load reminder state from disk."""
    global reminder_channel_id, reminder_message_template
    reminder_channel_id = state.get_reminder_channel()
    reminder_message_template = state.get_reminder_message()


# Initialize from disk
_load_reminder_state()


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
    state.set_reminder_channel(channel_id)
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
    state.set_reminder_message(trimmed)
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
