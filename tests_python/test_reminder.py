"""Tests for bot/reminder.py"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from bot import reminder
from bot.reminder import (
    get_dates_reminder_time,
    set_dates_reminder_channel,
    set_dates_reminder_message,
    format_dates_reminder_message,
    get_due_date_reminders,
    get_dates_reminder_channel,
    get_dates_reminder_message,
)


class TestGetDatesReminderTime:
    def test_returns_configured_time(self):
        reminder.reminder_hour, reminder.reminder_minute = 14, 30
        assert get_dates_reminder_time() == "14:30"


class TestSetDatesReminderChannel:
    def test_sets_valid_channel(self):
        with patch("bot.state.set_reminder_channel", return_value="123456789") as mock_save:
            result = set_dates_reminder_channel("123456789")
            assert result == "123456789"
            mock_save.assert_called_once_with("123456789")

    def test_rejects_non_string(self):
        with pytest.raises(ValueError, match="must be a valid Discord channel id"):
            set_dates_reminder_channel(123)

    def test_rejects_non_digits(self):
        with pytest.raises(ValueError, match="must be a valid Discord channel id"):
            set_dates_reminder_channel("abc")
        with pytest.raises(ValueError, match="must be a valid Discord channel id"):
            set_dates_reminder_channel("123abc")


class TestSetDatesReminderMessage:
    def test_sets_valid_message(self):
        msg = "Rappel raid aujourd'hui ({date})"
        with patch("bot.state.set_reminder_message", return_value=msg) as mock_save:
            assert set_dates_reminder_message(msg) == msg
            mock_save.assert_called_once_with(msg)

    def test_trims_whitespace(self):
        with patch("bot.state.set_reminder_message", return_value="test"):
            assert set_dates_reminder_message("  test  ") == "test"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            set_dates_reminder_message("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            set_dates_reminder_message("   ")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError, match="cannot exceed 2000"):
            set_dates_reminder_message("x" * 2001)

    def test_rejects_non_string(self):
        with pytest.raises(ValueError, match="must be a string"):
            set_dates_reminder_message(123)


class TestFormatDatesReminderMessage:
    def test_replaces_date_placeholder(self):
        set_dates_reminder_message("Rappel: {date}")
        assert format_dates_reminder_message("15/05/26") == "Rappel: 15/05/26"


class TestGetDatesReminderChannel:
    def test_returns_configured_channel(self):
        set_dates_reminder_channel("123456")
        assert get_dates_reminder_channel() == "123456"


class TestGetDatesReminderMessage:
    def test_returns_configured_message(self):
        set_dates_reminder_message("test message")
        assert get_dates_reminder_message() == "test message"


class TestGetDueDateReminders:
    def test_empty_when_time_does_not_match(self):
        mock_has_date = MagicMock(return_value=True)
        now = datetime(2026, 6, 15, 14, 0)
        result = get_due_date_reminders(mock_has_date, now)
        assert result == []

    def test_empty_when_no_date_for_today(self):
        reminder.reminder_hour, reminder.reminder_minute = 14, 0
        reminder.reminder_channel_id = "123456"
        mock_has_date = MagicMock(return_value=False)
        now = datetime(2026, 6, 15, 14, 0)
        result = get_due_date_reminders(mock_has_date, now)
        assert result == []

    def test_returns_reminder_when_time_matches(self):
        reminder.reminder_hour, reminder.reminder_minute = 10, 0
        reminder.reminder_channel_id = "123456"
        mock_has_date = MagicMock(return_value=True)
        now = datetime(2026, 6, 15, 10, 0)
        result = get_due_date_reminders(mock_has_date, now)
        assert len(result) == 1
        assert result[0]["channelId"] == "123456"
        assert "date" in result[0]

    def test_empty_when_no_channel(self):
        reminder.reminder_hour, reminder.reminder_minute = 10, 0
        reminder.reminder_channel_id = None
        mock_has_date = MagicMock(return_value=True)
        now = datetime(2026, 6, 15, 10, 0)
        result = get_due_date_reminders(mock_has_date, now)
        assert result == []
