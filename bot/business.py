"""Business logic coordinator — wires dates, reminders, and storage together."""

from datetime import datetime

from . import dates, storage, reminder


def _cleanup_past_dates_and_persist() -> None:
    """Remove past dates and persist to disk."""
    removed = dates.remove_past_dates()
    if removed:
        storage.write_dates_to_file(dates.get_raid_dates_snapshot())


def init_raid_helper() -> None:
    """Initialize the bot: load data from disk, clean up past dates."""
    stored = storage.load_dates_from_file()
    dates.hydrate_raid_dates(stored)
    _cleanup_past_dates_and_persist()


def save_raid_dates(dates_input: str) -> list[str]:
    """Add dates, clean up past, persist."""
    _cleanup_past_dates_and_persist()
    dates.save_raid_dates(dates_input)
    _cleanup_past_dates_and_persist()
    storage.write_dates_to_file(dates.get_raid_dates_snapshot())
    return dates.get_raid_dates_snapshot()


def delete_raid_dates(dates_input: str) -> list[str]:
    """Delete dates, clean up past, persist."""
    _cleanup_past_dates_and_persist()
    dates.delete_raid_dates(dates_input)
    storage.write_dates_to_file(dates.get_raid_dates_snapshot())
    return dates.get_raid_dates_snapshot()


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

# Initialize on import
init_raid_helper()
