"""Tests for bot/dates.py"""

import pytest
from datetime import datetime

from bot.dates import (
    is_valid_raid_date,
    to_sortable_timestamp,
    get_today_date_string,
    format_raid_date,
    format_discord_date_relative,
    raid_datetime_to_timestamp,
    hydrate_raid_dates,
    get_raid_dates_snapshot,
    has_raid_date,
    save_raid_dates,
    delete_raid_dates,
    display_raid_dates,
    set_dates_display_max,
    remove_past_dates,
)


@pytest.fixture(autouse=True)
def reset_dates():
    """Reset dates memory before each test."""
    import bot.dates as dates_module
    dates_module._dates_memory = []
    dates_module._display_max_dates = 10
    yield


class TestIsValidRaidDate:
    def test_accepts_valid_dates(self):
        assert is_valid_raid_date("01/01/26") is True
        assert is_valid_raid_date("31/12/26") is True
        assert is_valid_raid_date("15/05/26") is True
        assert is_valid_raid_date("29/02/24") is True  # leap year
        assert is_valid_raid_date("28/02/23") is True  # non-leap year

    def test_rejects_invalid_day(self):
        assert is_valid_raid_date("32/05/26") is False
        assert is_valid_raid_date("31/04/26") is False  # April has 30 days
        assert is_valid_raid_date("30/02/26") is False

    def test_rejects_invalid_month(self):
        assert is_valid_raid_date("15/00/26") is False
        assert is_valid_raid_date("15/13/26") is False

    def test_rejects_wrong_format(self):
        assert is_valid_raid_date("not-a-date") is False
        assert is_valid_raid_date("15/5/26") is False
        assert is_valid_raid_date("15-05-26") is False
        assert is_valid_raid_date("") is False
        assert is_valid_raid_date("150526") is False


class TestToSortableTimestamp:
    def test_sorts_correctly(self):
        assert to_sortable_timestamp("01/01/26") < to_sortable_timestamp("31/12/26")
        assert to_sortable_timestamp("31/12/25") < to_sortable_timestamp("01/01/26")
        assert to_sortable_timestamp("15/05/26") > to_sortable_timestamp("01/01/26")


class TestGetTodayDateString:
    def test_returns_dd_mm_yy_format(self):
        result = get_today_date_string(datetime(2026, 6, 15, 12, 0, 0))
        assert result == "15/06/26"

    def test_pads_single_digits(self):
        result = get_today_date_string(datetime(2026, 1, 5, 12, 0, 0))
        assert result == "05/01/26"


class TestSaveRaidDates:
    def test_adds_comma_separated_dates(self):
        save_raid_dates("15/05/26,22/05/26")
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_deduplicates(self):
        save_raid_dates("15/05/26,15/05/26")
        assert get_raid_dates_snapshot() == ["15/05/26"]

    def test_accepts_list_input(self):
        save_raid_dates(["15/05/26", "22/05/26"])
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_accepts_space_separated(self):
        save_raid_dates("15/05/26 22/05/26")
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_accepts_semicolon_separated(self):
        save_raid_dates("15/05/26;22/05/26")
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="No raid date provided"):
            save_raid_dates("")

    def test_rejects_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid raid date format"):
            save_raid_dates("invalid")

    def test_rejects_mixed_valid_invalid(self):
        with pytest.raises(ValueError, match="Invalid raid date format"):
            save_raid_dates("15/05/26,invalid")


class TestDeleteRaidDates:
    def test_deletes_existing(self):
        hydrate_raid_dates(["15/05/26", "22/05/26"])
        result = delete_raid_dates("15/05/26")
        assert result["deleted_dates"] == ["15/05/26"]
        assert result["dates"] == ["22/05/26"]

    def test_ignores_nonexistent(self):
        hydrate_raid_dates(["15/05/26", "22/05/26"])
        result = delete_raid_dates("01/01/26")
        assert result["deleted_dates"] == []
        assert result["dates"] == ["15/05/26", "22/05/26"]

    def test_deletes_multiple(self):
        hydrate_raid_dates(["15/05/26", "22/05/26"])
        result = delete_raid_dates("15/05/26,22/05/26")
        assert result["deleted_dates"] == ["15/05/26", "22/05/26"]
        assert result["dates"] == []

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="No raid date provided"):
            delete_raid_dates("")


class TestDisplayRaidDates:
    def test_no_dates_message(self):
        assert "Aucune date de raid" in display_raid_dates()

    def test_sorted_dates(self):
        hydrate_raid_dates(["15/05/26", "01/01/26", "31/12/26"])
        result = display_raid_dates()
        lines = [l for l in result.split("\n") if l.startswith("-")]
        assert lines == ["- 01/01/26", "- 15/05/26", "- 31/12/26"]

    def test_respects_max(self):
        set_dates_display_max(2)
        hydrate_raid_dates(["01/01/26", "15/05/26", "31/12/26"])
        result = display_raid_dates()
        lines = [l for l in result.split("\n") if l.startswith("-")]
        assert lines == ["- 01/01/26", "- 15/05/26"]


class TestSetDatesDisplayMax:
    def test_sets_valid_max(self):
        assert set_dates_display_max(5) == 5

    def test_rejects_zero(self):
        with pytest.raises(ValueError, match="Display max"):
            set_dates_display_max(0)

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="Display max"):
            set_dates_display_max(-1)

    def test_rejects_non_integer(self):
        with pytest.raises(ValueError, match="Display max"):
            set_dates_display_max(1.5)


class TestRemovePastDates:
    def test_removes_past_dates(self):
        future = datetime(2026, 6, 15, 0, 0, 0)
        hydrate_raid_dates(["01/06/26", "15/06/26", "01/07/26"])
        removed = remove_past_dates(future)
        assert removed == ["01/06/26"]
        assert get_raid_dates_snapshot() == ["15/06/26", "01/07/26"]

    def test_removes_nothing_when_future(self):
        future = datetime(2026, 6, 1, 0, 0, 0)
        hydrate_raid_dates(["15/06/26", "01/07/26"])
        removed = remove_past_dates(future)
        assert removed == []
        assert get_raid_dates_snapshot() == ["15/06/26", "01/07/26"]

    def test_removes_all_when_all_past(self):
        future = datetime(2026, 7, 1, 0, 0, 0)
        hydrate_raid_dates(["01/06/26", "15/06/26"])
        removed = remove_past_dates(future)
        assert sorted(removed) == ["01/06/26", "15/06/26"]
        assert get_raid_dates_snapshot() == []


class TestHydrateRaidDates:
    def test_loads_valid_dates(self):
        hydrate_raid_dates(["15/05/26", "22/05/26"])
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_filters_invalid(self):
        hydrate_raid_dates(["15/05/26", "invalid", "22/05/26"])
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_deduplicates(self):
        hydrate_raid_dates(["15/05/26", "15/05/26", "22/05/26"])
        assert get_raid_dates_snapshot() == ["15/05/26", "22/05/26"]

    def test_handles_empty(self):
        hydrate_raid_dates([])
        assert get_raid_dates_snapshot() == []

    def test_handles_non_list(self):
        hydrate_raid_dates("not-a-list")
        assert get_raid_dates_snapshot() == []


class TestHasRaidDate:
    def test_returns_true_for_existing(self):
        hydrate_raid_dates(["15/05/26", "22/05/26"])
        assert has_raid_date("15/05/26") is True
        assert has_raid_date("22/05/26") is True

    def test_returns_false_for_nonexistent(self):
        hydrate_raid_dates(["15/05/26", "22/05/26"])
        assert has_raid_date("01/01/26") is False


class TestFormatRaidDate:
    def test_format_lundi(self):
        # 14 sept 2026 = lundi
        assert format_raid_date("14/09/26") == "Lundi 14 Sept."

    def test_format_mercredi(self):
        # 7 janv 2026 = mercredi
        assert format_raid_date("07/01/26") == "Mercredi 7 Janv."

    def test_format_vendredi(self):
        # 15 mai 2026 = vendredi
        assert format_raid_date("15/05/26") == "Vendredi 15 Mai"
        # 22 mai 2026 = vendredi
        assert format_raid_date("22/05/26") == "Vendredi 22 Mai"

    def test_format_janvier(self):
        # 1 janv 2026 = jeudi
        assert format_raid_date("01/01/26") == "Jeudi 1 Janv."

    def test_format_decembre(self):
        # 31 déc 2026 = jeudi
        assert format_raid_date("31/12/26") == "Jeudi 31 Déc."

    def test_format_single_digit_day(self):
        # 5 janv 2026 = lundi
        assert format_raid_date("05/01/26") == "Lundi 5 Janv."


class TestRaidDatetimeToTimestamp:
    def test_returns_timestamp(self):
        # Doit retourner un timestamp Unix valide
        timestamp = raid_datetime_to_timestamp("03/09/26")
        assert isinstance(timestamp, int)
        assert timestamp > 1700000000  # After 2024


class TestFormatDiscordDateRelative:
    def test_format_relative(self):
        result = format_discord_date_relative("03/09/26")
        assert result.startswith("<t:")
        assert result.endswith(":R>")

    def test_format_relative_structure(self):
        result = format_discord_date_relative("03/09/26")
        import re
        match = re.match(r"<t:(\d+):R>", result)
        assert match is not None
        assert int(match.group(1)) > 0
