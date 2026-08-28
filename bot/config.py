"""Static configuration — loaded from config.json at startup.

Values here are "locked": they can only be changed by editing config.json
and restarting the bot. Each value is validated on load; invalid values
fall back to defaults with a warning.
"""

import json
import os

__all__ = ["load_config", "get"]

# --- Paths ---

def _get_data_dir_path():
    """Return the path to the data directory."""
    return os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "data"))


def _get_config_file_path():
    """Return the path to the config.json file."""
    return os.path.join(_get_data_dir_path(), "config.json")


# --- Defaults ---

_DEFAULTS = {
    "raid": {
        "days": ["tuesday", "thursday"],
    },
    "reminder": {
        "time": "10:00",
    },
    "poll": {
        "message": "Session bonus ?",
        "durationHours": 48,
        "sendHour": 21,
        "sendMinute": 0,
    },
    "calendar": {
        "title": "🔔 Prochaines sessions 🔔",
        "color": 3900150,
    },
}

# --- Validators ---

_DAY_NAMES = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}

_VALIDATORS = {
    "raid.days": lambda v: isinstance(v, list) and all(isinstance(d, str) and d.lower() in _DAY_NAMES for d in v),
    "reminder.time": lambda v: isinstance(v, str) and len(v) == 5 and v[2] == ":" and v[:2].isdigit() and v[3:].isdigit(),
    "poll.message": lambda v: isinstance(v, str) and len(v) > 0 and len(v) <= 200,
    "poll.durationHours": lambda v: isinstance(v, int) and 1 <= v <= 1008,
    "poll.sendHour": lambda v: isinstance(v, int) and 0 <= v <= 23,
    "poll.sendMinute": lambda v: isinstance(v, int) and 0 <= v <= 59,
    "calendar.title": lambda v: isinstance(v, str) and len(v) > 0 and len(v) <= 256,
    "calendar.color": lambda v: isinstance(v, int) and 0 <= v <= 0xFFFFFF,
}


def _get_nested(data: dict, key: str):
    """Get a nested value from a dict using dot notation."""
    keys = key.split(".")
    for k in keys:
        if isinstance(data, dict):
            data = data.get(k)
        else:
            return None
    return data


def _set_nested(data: dict, key: str, value):
    """Set a nested value in a dict using dot notation."""
    keys = key.split(".")
    d = data
    for k in keys[:-1]:
        if k not in d or not isinstance(d[k], dict):
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value
    return data


# --- Config loading ---

_config = None  # Cached config


def load_config() -> dict:
    """Load config.json, validate, fallback on defaults, log warnings.

    Returns:
        Validated config dict.
    """
    global _config

    if _config is not None:
        return _config

    _config = {}

    # Try to load config.json
    try:
        config_file = _get_config_file_path()
        if not os.path.exists(config_file):
            print(f"[config] config.json not found, using defaults")
            _config = json.loads(json.dumps(_DEFAULTS))  # deep copy
            return _config

        with open(config_file, "r", encoding="utf-8") as f:
            data = json.loads(f.read()) or {}
    except (json.JSONDecodeError, OSError) as e:
        print(f"[config] Error loading config.json: {e}, using defaults")
        _config = json.loads(json.dumps(_DEFAULTS))
        return _config

    # Validate and merge with defaults
    _config = json.loads(json.dumps(_DEFAULTS))  # deep copy of defaults

    for key, validator in _VALIDATORS.items():
        value = _get_nested(data, key)
        if value is not None:
            if not validator(value):
                default = _get_nested(_DEFAULTS, key)
                print(f"[config] Invalid value for {key}: {value}, using default {default}")
            else:
                _set_nested(_config, key, value)

    return _config


def get(key: str):
    """Get a config value using dot notation.

    Args:
        key: Dot-separated key (e.g., "poll.durationHours").

    Returns:
        The config value (always present, falls back to _DEFAULTS).
    """
    if _config is None:
        load_config()
    return _get_nested(_config, key)
