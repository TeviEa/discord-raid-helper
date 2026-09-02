"""Date management: validation, CRUD, display, sorting."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

__all__ = [
    "is_valid_raid_date",
    "to_sortable_timestamp",
    "get_today_date_string",
    "format_raid_date",
    "format_discord_date_relative",
    "raid_datetime_to_timestamp",
    "hydrate_raid_dates",
    "get_raid_dates_snapshot",
    "has_raid_date",
    "save_raid_dates",
    "delete_raid_dates",
    "display_raid_dates",
    "set_dates_display_max",
    "remove_past_dates",
]

_dates_memory: list[str] = []
_display_max_dates: int = 10

_DATE_RE = re.compile(r"^(\d{2})/(\d{2})/(\d{2})$")

_DAYS_FR = {
    0: "Lundi", 1: "Mardi", 2: "Mercredi", 3: "Jeudi",
    4: "Vendredi", 5: "Samedi", 6: "Dimanche",
}

_MONTHS_FR = {
    1: "Janv.", 2: "Févr.", 3: "Mars", 4: "Avr.",
    5: "Mai", 6: "Juin", 7: "Juil", 8: "Août",
    9: "Sept.", 10: "Oct.", 11: "Nov.", 12: "Déc.",
}

_PARIS = ZoneInfo("Europe/Paris")


def format_raid_date(date_string: str) -> str:
    """Format a DD/MM/YY date string to French: 'Lundi 14 Sept.'.

    Args:
        date_string: Date in DD/MM/YY format.

    Returns:
        Formatted date string in French.
    """
    day, month, year = (int(p) for p in date_string.split("/"))
    dt = datetime(2000 + year, month, day)
    return f"{_DAYS_FR[dt.weekday()]} {day} {_MONTHS_FR[month]}"


def raid_datetime_to_timestamp(date_string: str) -> int:
    """Convert a DD/MM/YY raid date to Unix timestamp (seconds).

    Uses the configured raid time from config.py, with Europe/Paris timezone
    to handle DST correctly.

    Args:
        date_string: Date in DD/MM/YY format.

    Returns:
        Unix timestamp in seconds (UTC).
    """
    from . import config

    raid_time_str = config.get("raid.time")
    raid_hour, raid_minute = map(int, raid_time_str.split(":"))

    day, month, year = (int(p) for p in date_string.split("/"))
    local_dt = datetime(2000 + year, month, day, raid_hour, raid_minute, tzinfo=_PARIS)
    return int(local_dt.timestamp())


def format_discord_date_relative(date_string: str) -> str:
    """Format a DD/MM/YY date string to Discord relative format.

    Args:
        date_string: Date in DD/MM/YY format.

    Returns:
        Discord timestamp string: '<t:TIMESTAMP:R>'
    """
    timestamp = raid_datetime_to_timestamp(date_string)
    return f"<t:{timestamp}:R>"


def is_valid_raid_date(date_string: str) -> bool:
    """Check if a date string is in valid DD/MM/YY format."""
    match = _DATE_RE.match(date_string)
    if not match:
        return False

    day, month, year = map(int, match.groups())
    full_year = 2000 + year

    try:
        datetime(full_year, month, day)
        return True
    except ValueError:
        return False


def to_sortable_timestamp(date_string: str) -> int:
    """Convert a DD/MM/YY date string to a sortable integer timestamp."""
    day, month, year = (int(p) for p in date_string.split("/"))
    return datetime(2000 + year, month, day).timestamp()


def get_today_date_string(now: datetime | None = None) -> str:
    """Get today's date as DD/MM/YY string using local time."""
    now = now or datetime.now()
    return now.strftime("%d/%m/%y")


def hydrate_raid_dates(raw_dates: list) -> None:
    """Load dates from a list, filtering invalid/duplicates."""
    global _dates_memory
    _dates_memory = []

    if not isinstance(raw_dates, list):
        return

    for date in raw_dates:
        if isinstance(date, str) and is_valid_raid_date(date) and date not in _dates_memory:
            _dates_memory.append(date)


def get_raid_dates_snapshot() -> list[str]:
    """Return a copy of the current dates."""
    return list(_dates_memory)


def has_raid_date(date: str) -> bool:
    """Check if a date exists in memory."""
    return date in _dates_memory


def remove_past_dates(now: datetime | None = None) -> list[str]:
    """Remove dates before today. Returns the removed dates."""
    global _dates_memory
    now = now or datetime.now()
    today_start = datetime(now.year, now.month, now.day).timestamp()
    removed = []

    for i in range(len(_dates_memory) - 1, -1, -1):
        if to_sortable_timestamp(_dates_memory[i]) < today_start:
            removed.append(_dates_memory[i])
            _dates_memory.pop(i)

    return removed


def set_dates_display_max(max_dates) -> int:
    """Set the maximum number of dates to display."""
    if isinstance(max_dates, float):
        raise ValueError("Display max must be an integer greater than or equal to 1")
    parsed_max = int(max_dates)
    if parsed_max < 1:
        raise ValueError("Display max must be an integer greater than or equal to 1")
    global _display_max_dates
    _display_max_dates = parsed_max
    return _display_max_dates


def save_raid_dates(dates_input: str | list[str]) -> list[str]:
    """Add valid dates to memory."""
    dates = normalize_input(dates_input)

    if not dates:
        raise ValueError("No raid date provided")

    invalid = [d for d in dates if not is_valid_raid_date(d)]
    if invalid:
        raise ValueError(f"Invalid raid date format: {', '.join(invalid)}")

    for date in dates:
        if date not in _dates_memory:
            _dates_memory.append(date)

    return get_raid_dates_snapshot()


def delete_raid_dates(dates_input: str | list[str]) -> dict:
    """Remove dates from memory. Returns {dates, deleted_dates}."""
    dates = normalize_input(dates_input)

    if not dates:
        raise ValueError("No raid date provided")

    deleted = []
    for date in dates:
        try:
            _dates_memory.remove(date)
            deleted.append(date)
        except ValueError:
            pass

    return {"dates": get_raid_dates_snapshot(), "deleted_dates": deleted}


def display_raid_dates() -> str:
    """Display formatted raid dates."""
    if not _dates_memory:
        return "Aucune date de raid enregistree pour le moment."

    sorted_dates = sorted(_dates_memory, key=to_sortable_timestamp)
    displayed = sorted_dates[:_display_max_dates]
    lines = [f"- {d}" for d in displayed]
    return "Prochaines dates de raid:\n" + "\n".join(lines)


def normalize_input(dates_input: str | list[str]) -> list[str]:
    """Parse input into a list of date strings."""
    if isinstance(dates_input, list):
        return dates_input

    if not isinstance(dates_input, str):
        raise TypeError("dates_input must be a string or a list of strings")

    return [d.strip() for d in re.split(r"[\s,;]+", dates_input) if d.strip()]
