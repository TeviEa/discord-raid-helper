"""Tests for the calendar feature."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot import calendar
from bot.dates import get_today_date_string


class TestSetCalendarChannel:
    """Tests for set_calendar_channel."""

    def test_sets_valid_channel(self):
        with patch("bot.calendar._save_calendar_config"):
            result = calendar.set_calendar_channel("123456789")
            assert result == "123456789"
            assert calendar.get_calendar_channel() == "123456789"

    def test_rejects_non_string(self):
        with patch("bot.calendar._save_calendar_config"):
            with pytest.raises(ValueError, match="valid Discord channel ID"):
                calendar.set_calendar_channel(123456789)

    def test_rejects_non_digits(self):
        with patch("bot.calendar._save_calendar_config"):
            with pytest.raises(ValueError, match="valid Discord channel ID"):
                calendar.set_calendar_channel("abc123")

    def test_allows_none_to_disable(self):
        with patch("bot.calendar._save_calendar_config"), \
             patch.object(calendar, "_schedule_old_message_deletion"):
            result = calendar.set_calendar_channel(None)
            assert result is None
            assert calendar.get_calendar_channel() is None

    def test_does_not_delete_on_same_channel(self):
        with patch("bot.calendar._save_calendar_config"), \
             patch.object(calendar, "_schedule_old_message_deletion"):
            calendar.set_calendar_channel("111111111")
            assert calendar.get_calendar_channel() == "111111111"

    def test_does_not_delete_on_first_setup(self):
        calendar._calendar_channel_id = None
        with patch("bot.calendar._save_calendar_config"), \
             patch.object(calendar, "_schedule_old_message_deletion"):
            calendar.set_calendar_channel("111111111")
            assert calendar.get_calendar_channel() == "111111111"

    @pytest.mark.asyncio
    async def test_resets_message_id_on_channel_change(self):
        calendar._calendar_channel_id = "111111111"
        calendar._calendar_message_id = "old_message_id"
        with patch("bot.calendar._save_calendar_config"), \
             patch.object(calendar, "_delete_message", new_callable=AsyncMock) as mock_delete:
            calendar.set_calendar_channel("999999999")
            assert calendar.get_calendar_channel() == "999999999"
            assert calendar._calendar_message_id is None
            mock_delete.assert_called_once_with("111111111", "old_message_id")


class TestSetCalendarTitle:
    """Tests for set_calendar_title."""

    def test_sets_valid_title(self):
        with patch("bot.calendar._save_calendar_config"):
            result = calendar.set_calendar_title("Mon Calendrier")
            assert result == "Mon Calendrier"
            assert calendar.get_calendar_title() == "Mon Calendrier"

    def test_trims_whitespace(self):
        with patch("bot.calendar._save_calendar_config"):
            result = calendar.set_calendar_title("  Mon calendrier  ")
            assert result == "Mon calendrier"

    def test_rejects_empty(self):
        with patch("bot.calendar._save_calendar_config"):
            with pytest.raises(ValueError, match="cannot be empty"):
                calendar.set_calendar_title("")

    def test_rejects_whitespace_only(self):
        with patch("bot.calendar._save_calendar_config"):
            with pytest.raises(ValueError, match="cannot be empty"):
                calendar.set_calendar_title("   ")

    def test_rejects_too_long(self):
        with patch("bot.calendar._save_calendar_config"):
            with pytest.raises(ValueError, match="cannot exceed 256"):
                calendar.set_calendar_title("x" * 257)

    def test_accepts_max_length(self):
        with patch("bot.calendar._save_calendar_config"):
            result = calendar.set_calendar_title("x" * 256)
            assert result == "x" * 256


class TestSetCalendarColor:
    """Tests for set_calendar_color."""

    def test_sets_valid_color(self):
        with patch("bot.calendar._save_calendar_config"):
            result = calendar.set_calendar_color(0xFF0000)
            assert result == 0xFF0000
            assert calendar.get_calendar_color() == 0xFF0000

    def test_sets_decimal_color(self):
        with patch("bot.calendar._save_calendar_config"):
            result = calendar.set_calendar_color(16711680)
            assert result == 16711680


class TestBuildCalendarEmbed:
    """Tests for build_calendar_embed."""

    def test_embed_has_title(self):
        calendar._calendar_title = "Mon Calendrier"
        try:
            with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
                embed = calendar.build_calendar_embed()
                assert embed["title"] == "Mon Calendrier"
        finally:
            calendar._calendar_title = "Calendrier des raids"

    def test_embed_has_description(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26", "22/05/26"]):
            embed = calendar.build_calendar_embed()
            assert "15/05/26" in embed["description"]
            assert "22/05/26" in embed["description"]

    def test_embed_highlights_today(self):
        today = get_today_date_string()
        with patch("bot.dates.get_raid_dates_snapshot", return_value=[today]):
            embed = calendar.build_calendar_embed()
            assert f"**{today}** (aujourd'hui)" in embed["description"]

    def test_embed_has_color(self):
        calendar._calendar_color = 0xFF0000
        try:
            with patch("bot.dates.get_raid_dates_snapshot", return_value=[]):
                embed = calendar.build_calendar_embed()
                assert embed["color"] == 0xFF0000
        finally:
            calendar._calendar_color = 0x3B82F6

    def test_embed_has_footer(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=[]):
            embed = calendar.build_calendar_embed()
            assert "footer" in embed
            assert "text" in embed["footer"]
            assert "Mis a jour le" in embed["footer"]["text"]

    def test_embed_no_dates_message(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=[]):
            embed = calendar.build_calendar_embed()
            assert embed["description"] == "Aucune date de raid enregistree."

    def test_embed_sorted_dates(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["22/05/26", "15/05/26"]):
            embed = calendar.build_calendar_embed()
            lines = embed["description"].split("\n")
            date_lines = [l for l in lines if l.startswith("- ")]
            assert date_lines[0] == "- 15/05/26"
            assert date_lines[1] == "- 22/05/26"


class TestPostCalendarMessage:
    """Tests for post_calendar_message."""

    @pytest.mark.asyncio
    async def test_posts_message(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", None):
                with patch("bot.discord_api.discord_request", return_value={"id": "msg_123"}):
                    with patch.object(calendar, "build_calendar_embed", return_value={"title": "Test"}):
                        result = await calendar.post_calendar_message()
                        assert result == {"channel_id": "123456789", "message_id": "msg_123"}
                        assert calendar._calendar_message_id == "msg_123"

    @pytest.mark.asyncio
    async def test_returns_none_without_channel(self):
        with patch("bot.calendar._calendar_channel_id", None):
            result = await calendar.post_calendar_message()
            assert result is None

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        with patch("bot.calendar._calendar_channel_id", "123456789"):
            with patch("bot.discord_api.discord_request", side_effect=Exception("API error")):
                with patch.object(calendar, "build_calendar_embed"):
                    result = await calendar.post_calendar_message()
                    assert result is None


class TestDeleteCalendarMessage:
    """Tests for delete_calendar_message."""

    @pytest.mark.asyncio
    async def test_deletes_message(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", "msg_123"):
                with patch("bot.discord_api.discord_request", new_callable=AsyncMock) as mock_request:
                    result = await calendar.delete_calendar_message()
                    assert result is True
                    assert calendar._calendar_message_id is None
                    mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_false_without_channel(self):
        with patch("bot.calendar._calendar_channel_id", None):
            result = await calendar.delete_calendar_message()
            assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_without_message_id(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", None):
                result = await calendar.delete_calendar_message()
                assert result is False

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", "msg_123"):
                with patch("bot.discord_api.discord_request", side_effect=Exception("API error")):
                    result = await calendar.delete_calendar_message()
                    assert result is False


class TestUpdateCalendarMessage:
    """Tests for update_calendar_message."""

    @pytest.mark.asyncio
    async def test_edits_existing_message(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", "msg_123"):
                with patch("bot.discord_api.discord_request", return_value={"id": "msg_123"}):
                    with patch.object(calendar, "build_calendar_embed", return_value={"title": "Test"}):
                        result = await calendar.update_calendar_message()
                        assert result == {"channel_id": "123456789", "message_id": "msg_123"}

    @pytest.mark.asyncio
    async def test_posts_new_when_no_message_id(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", None):
                with patch.object(calendar, "post_calendar_message", new_callable=AsyncMock, return_value={"channel_id": "123456789", "message_id": "msg_456"}):
                    result = await calendar.update_calendar_message()
                    assert result == {"channel_id": "123456789", "message_id": "msg_456"}

    @pytest.mark.asyncio
    async def test_returns_none_without_channel(self):
        with patch.object(calendar, "_calendar_channel_id", None):
            result = await calendar.update_calendar_message()
            assert result is None

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        with patch.object(calendar, "_calendar_channel_id", "123456789"):
            with patch.object(calendar, "_calendar_message_id", "msg_123"):
                with patch("bot.discord_api.discord_request", side_effect=Exception("API error")):
                    with patch.object(calendar, "build_calendar_embed"):
                        result = await calendar.update_calendar_message()
                        assert result is None


class TestGetCalendarConfig:
    """Tests for get_calendar_config."""

    def test_returns_config(self):
        calendar._calendar_channel_id = "123456789"
        calendar._calendar_message_id = "msg_123"
        calendar._calendar_title = "Mon Calendrier"
        calendar._calendar_color = 0xFF0000
        try:
            config = calendar.get_calendar_config()
            assert config["channel"] == "123456789"
            assert config["message_id"] == "msg_123"
            assert config["title"] == "Mon Calendrier"
            assert config["color"] == 0xFF0000
        finally:
            calendar._calendar_channel_id = None
            calendar._calendar_message_id = None
            calendar._calendar_title = "Calendrier des raids"
            calendar._calendar_color = 0x3B82F6

    def test_returns_defaults(self):
        calendar._calendar_channel_id = None
        calendar._calendar_message_id = None
        calendar._calendar_title = "Calendrier des raids"
        calendar._calendar_color = 0x3B82F6
        config = calendar.get_calendar_config()
        assert config["channel"] is None
        assert config["message_id"] is None
        assert config["title"] == "Calendrier des raids"
        assert config["color"] == 0x3B82F6


class TestDeleteOldMessage:
    """Tests for _delete_message and _schedule_old_message_deletion."""

    @pytest.mark.asyncio
    async def test_deletes_message(self):
        with patch("bot.discord_api.discord_request", new_callable=AsyncMock) as mock_request:
            await calendar._delete_message("123456789", "msg_123")
            mock_request.assert_called_once_with(
                "channels/123456789/messages/msg_123",
                method="DELETE",
            )

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        with patch("bot.discord_api.discord_request", side_effect=Exception("API error")):
            # Should not raise
            await calendar._delete_message("123456789", "msg_123")

    @pytest.mark.asyncio
    async def test_schedules_deletion(self):
        with patch.object(calendar, "_delete_message", new_callable=AsyncMock) as mock_delete:
            calendar._schedule_old_message_deletion("123456789", "msg_123")
            assert calendar._deletion_task is not None
            assert not calendar._deletion_task.done()
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_schedule_duplicate_deletion(self):
        mock_task = AsyncMock()
        mock_task.done = lambda: False

        calendar._deletion_task = mock_task
        calendar._schedule_old_message_deletion("123456789", "msg_123")
        # Should still be the same task
        assert calendar._deletion_task is mock_task


class TestSaveCalendarConfig:
    """Tests for _save_calendar_config."""

    def test_saves_to_storage(self):
        calendar._calendar_channel_id = "123456789"
        calendar._calendar_message_id = "msg_123"
        calendar._calendar_title = "Mon Calendrier"
        calendar._calendar_color = 0xFF0000

        with patch("bot.calendar.storage.load_data", return_value={}):
            with patch("bot.calendar.storage.save_data") as mock_save:
                calendar._save_calendar_config()
                mock_save.assert_called_once()
                saved_data = mock_save.call_args[0][0]
                assert saved_data["calendar"]["channelId"] == "123456789"
                assert saved_data["calendar"]["messageId"] == "msg_123"
                assert saved_data["calendar"]["title"] == "Mon Calendrier"
                assert saved_data["calendar"]["color"] == 0xFF0000
