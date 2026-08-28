"""Dynamic state — loaded from and written to state.json.

This file manages all "live" configuration that can be changed via Discord
commands without restarting the bot. It also stores auto-managed state
(lastSentDate, messageId, etc.).
"""

import json
import os
import tempfile

__all__ = [
    "load_state",
    "save_state",
    # Dates
    "get_dates",
    "set_dates",
    # Reminder
    "get_reminder_channel",
    "set_reminder_channel",
    "get_reminder_message",
    "set_reminder_message",
    "set_reminder_last_sent",
    # Poll
    "get_poll_day",
    "set_poll_day",
    "get_poll_channel",
    "set_poll_channel",
    "get_poll_ping_role",
    "set_poll_ping_role",
    "get_poll_pause_enabled",
    "set_poll_pause_enabled",
    "get_poll_pause_until",
    "set_poll_pause_until",
    "get_poll_last_sent",
    "set_poll_last_sent",
    # Calendar
    "get_calendar_channel",
    "set_calendar_channel",
    "get_calendar_message_id",
    "set_calendar_message_id",
]


# --- Paths ---

def _get_data_dir_path():
    """Return the path to the data directory."""
    return os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))


def _get_state_file_path():
    """Return the path to the state.json file."""
    return os.path.join(_get_data_dir_path(), "state.json")


# --- Core ---

_state = None  # Cached state


def load_state() -> dict:
    """Load state.json. Returns {} on any error."""
    global _state

    if _state is not None:
        return _state

    try:
        state_file = _get_state_file_path()
        if not os.path.exists(state_file):
            _state = {}
            return _state
        with open(state_file, "r", encoding="utf-8") as f:
            _state = json.loads(f.read()) or {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"[state] Error loading state.json: {e}, starting fresh")
        _state = {}

    return _state


def save_state(state: dict | None = None) -> None:
    """Save state to state.json using atomic write.

    If state is None, saves the cached _state.
    """
    data = state if state is not None else _state
    if data is None:
        data = {}

    try:
        data_dir = _get_data_dir_path()
        os.makedirs(data_dir, exist_ok=True)

        state_file = _get_state_file_path()
        fd, tmp_path = tempfile.mkstemp(dir=data_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, state_file)
        except Exception:
            os.unlink(tmp_path)
            raise
    except Exception as e:
        print(f"[state] Unable to write state.json: {e}")


# --- Helper ---

def _get_nested(data: dict, key: str, default=None):
    """Get a nested value from a dict using dot notation."""
    keys = key.split(".")
    d = data
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default


def _set_nested(data: dict, key: str, value) -> dict:
    """Set a nested value in a dict using dot notation."""
    keys = key.split(".")
    d = data
    for k in keys[:-1]:
        if k not in d or not isinstance(d[k], dict):
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value
    return data


# --- Dates ---

def get_dates() -> list:
    """Get the list of raid dates."""
    state = load_state()
    return state.get("dates", []) if isinstance(state.get("dates"), list) else []


def set_dates(dates: list) -> None:
    """Set the list of raid dates."""
    state = load_state()
    state["dates"] = dates
    save_state(state)


# --- Reminder ---

def get_reminder_channel() -> str | None:
    """Get the reminder channel ID."""
    return _get_nested(load_state(), "reminder.channelId")


def set_reminder_channel(channel_id: str | None) -> str | None:
    """Set the reminder channel ID."""
    state = load_state()
    state = _set_nested(state, "reminder.channelId", channel_id)
    save_state(state)
    return channel_id


def get_reminder_message() -> str:
    """Get the reminder message template."""
    return _get_nested(load_state(), "reminder.message", "")


def set_reminder_message(message: str) -> str:
    """Set the reminder message template."""
    state = load_state()
    state = _set_nested(state, "reminder.message", message)
    save_state(state)
    return message


def set_reminder_last_sent(date: str) -> None:
    """Set the last date a reminder was sent."""
    state = load_state()
    state = _set_nested(state, "reminder.lastSentDate", date)
    save_state(state)


# --- Poll ---

def get_poll_day() -> str:
    """Get the poll day of week."""
    return _get_nested(load_state(), "poll.day", "")


def set_poll_day(day: str) -> str:
    """Set the poll day of week."""
    state = load_state()
    state = _set_nested(state, "poll.day", day)
    save_state(state)
    return day


def get_poll_channel() -> str | None:
    """Get the poll channel ID."""
    return _get_nested(load_state(), "poll.channelId")


def set_poll_channel(channel_id: str | None) -> str | None:
    """Set the poll channel ID."""
    state = load_state()
    state = _set_nested(state, "poll.channelId", channel_id)
    save_state(state)
    return channel_id


def get_poll_ping_role() -> str | None:
    """Get the poll ping role ID."""
    return _get_nested(load_state(), "poll.pingRoleId")


def set_poll_ping_role(role_id: str | None) -> str | None:
    """Set the poll ping role ID."""
    state = load_state()
    state = _set_nested(state, "poll.pingRoleId", role_id)
    save_state(state)
    return role_id


def get_poll_pause_enabled() -> bool:
    """Get the poll pause enabled state."""
    return _get_nested(load_state(), "poll.pauseEnabled", False)


def set_poll_pause_enabled(enabled: bool) -> bool:
    """Set the poll pause enabled state."""
    state = load_state()
    state = _set_nested(state, "poll.pauseEnabled", enabled)
    save_state(state)
    return enabled


def get_poll_pause_until() -> str:
    """Get the poll pause until date."""
    return _get_nested(load_state(), "poll.pauseUntil", "")


def set_poll_pause_until(until: str) -> str:
    """Set the poll pause until date."""
    state = load_state()
    state = _set_nested(state, "poll.pauseUntil", until)
    save_state(state)
    return until


def set_poll_last_sent(date: str) -> None:
    """Set the last date a poll was sent."""
    state = load_state()
    state = _set_nested(state, "poll.lastSentDate", date)
    save_state(state)


# --- Calendar ---

def get_calendar_channel() -> str | None:
    """Get the calendar channel ID."""
    return _get_nested(load_state(), "calendar.channelId")


def set_calendar_channel(channel_id: str | None) -> str | None:
    """Set the calendar channel ID."""
    state = load_state()
    state = _set_nested(state, "calendar.channelId", channel_id)
    save_state(state)
    return channel_id


def get_calendar_message_id() -> str | None:
    """Get the calendar message ID."""
    return _get_nested(load_state(), "calendar.messageId")


def set_calendar_message_id(message_id: str | None) -> None:
    """Set the calendar message ID."""
    state = load_state()
    state = _set_nested(state, "calendar.messageId", message_id)
    save_state(state)
