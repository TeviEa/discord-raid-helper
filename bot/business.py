"""Business logic coordinator — wires dates, reminders, and storage together."""

from datetime import datetime

from . import dates, storage, reminder, calendar, poll


def _cleanup_past_dates_and_persist() -> None:
    """Remove past dates and persist to disk."""
    removed = dates.remove_past_dates()
    if removed:
        storage.write_dates_to_file(dates.get_raid_dates_snapshot())


def daily_check() -> bool:
    """Run the daily check: cleanup past dates, update calendar, and send poll.

    Returns:
        True if today is a raid date, False otherwise.
    """
    _cleanup_past_dates_and_persist()
    return dates.has_raid_date(dates.get_today_date_string())


def init_raid_helper() -> None:
    """Initialize the bot: load data from disk, clean up past dates, restore calendar and poll config."""
    stored = storage.load_dates_from_file()
    dates.hydrate_raid_dates(stored)
    _cleanup_past_dates_and_persist()

    config = calendar._load_calendar_config()
    calendar._calendar_channel_id = config.get("channelId")
    calendar._calendar_message_id = config.get("messageId")
    calendar._calendar_title = config.get("title", "Calendrier des raids")
    calendar._calendar_color = config.get("color", 0x3B82F6)

    poll.init_poll()


def save_raid_dates(dates_input: str) -> list[str]:
    """Add dates, clean up past, persist."""
    _cleanup_past_dates_and_persist()
    dates.save_raid_dates(dates_input)
    _cleanup_past_dates_and_persist()
    storage.write_dates_to_file(dates.get_raid_dates_snapshot())
    _schedule_calendar_update()
    return dates.get_raid_dates_snapshot()


def delete_raid_dates(dates_input: str) -> list[str]:
    """Delete dates, clean up past, persist."""
    _cleanup_past_dates_and_persist()
    dates.delete_raid_dates(dates_input)
    storage.write_dates_to_file(dates.get_raid_dates_snapshot())
    _schedule_calendar_update()
    return dates.get_raid_dates_snapshot()


# Track pending calendar update tasks to avoid duplicates
_calendar_update_task = None


def _schedule_calendar_update() -> None:
    """Schedule a background calendar update if one is not already pending."""
    global _calendar_update_task
    if _calendar_update_task is not None and not _calendar_update_task.done():
        return
    import asyncio

    _calendar_update_task = asyncio.create_task(calendar.update_calendar_message())


def display_raid_dates() -> str:
    """Display formatted raid dates with cleanup."""
    _cleanup_past_dates_and_persist()
    return dates.display_raid_dates()


def get_due_date_reminders(now: datetime | None = None) -> list[dict]:
    """Get due reminders with cleanup."""
    _cleanup_past_dates_and_persist()
    return reminder.get_due_date_reminders(dates.has_raid_date, now)


# Re-export for convenience
from .dates import set_dates_display_max, get_raid_dates_snapshot
from .reminder import (
    set_dates_reminder_time,
    get_dates_reminder_time,
    set_dates_reminder_channel,
    set_dates_reminder_message,
    format_dates_reminder_message,
    get_dates_reminder_channel,
    get_dates_reminder_message,
)
from .calendar import (
    set_calendar_channel,
    get_calendar_channel,
    set_calendar_title,
    get_calendar_title,
    set_calendar_color,
    get_calendar_color,
    build_calendar_embed,
    post_calendar_message,
    delete_calendar_message,
    update_calendar_message,
    get_calendar_config,
)
from .poll import (
    set_poll_day,
    get_poll_day,
    set_poll_channel,
    get_poll_channel,
    set_poll_message,
    get_poll_message,
    set_poll_pause,
    get_poll_pause,
    set_poll_pause_until,
    get_poll_pause_until,
    set_poll_ping_role,
    get_poll_ping_role,
    build_poll_message,
    post_poll_message,
    get_poll_config,
)


def set_calendar_message(message: str) -> str:
    """Set the calendar embed title and update the posted message."""
    updated = calendar.set_calendar_title(message)
    _schedule_calendar_update()
    return updated

# Initialize on import
init_raid_helper()
