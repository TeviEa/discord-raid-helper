"""JSON file persistence layer."""

import json
import os
import tempfile

__all__ = ["load_data", "save_data", "load_dates_from_file", "write_dates_to_file"]


def _get_data_dir_path():
    """Return the path to the data directory."""
    return os.path.join(os.path.dirname(__file__), "data")


def _get_data_file_path():
    """Return the path to the values.json file."""
    return os.path.join(_get_data_dir_path(), "values.json")


def load_data() -> dict:
    """Load data from the JSON file. Returns {} on any error."""
    try:
        data_file = _get_data_file_path()
        if not os.path.exists(data_file):
            return {}
        with open(data_file, "r", encoding="utf-8") as f:
            return json.loads(f.read()) or {}
    except Exception as e:
        print(f"[{__name__}] Unable to read data file {_get_data_file_path()}: {e}")
        return {}


def save_data(data: dict) -> None:
    """Save data to the JSON file using atomic write."""
    try:
        data_dir = _get_data_dir_path()
        os.makedirs(data_dir, exist_ok=True)

        data_file = _get_data_file_path()
        # Atomic write: write to temp file then rename
        fd, tmp_path = tempfile.mkstemp(dir=data_dir, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, data_file)
        except Exception:
            os.unlink(tmp_path)
            raise
    except Exception as e:
        print(f"[{__name__}] Unable to write data file {_get_data_file_path()}: {e}")


def load_dates_from_file() -> list:
    """Load the dates array from the data file."""
    data = load_data()
    return data.get("dates", []) if isinstance(data.get("dates"), list) else []


def write_dates_to_file(dates: list) -> None:
    """Write the dates array to the data file."""
    data = load_data()
    data["dates"] = dates
    save_data(data)
