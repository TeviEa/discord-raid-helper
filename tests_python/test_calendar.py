"""Tests for the calendar feature."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot import calendar
from bot.dates import get_today_date_string


class TestSetCalendarChannel:
    """Tests for set_calendar_channel."""

    def test_sets_valid_channel(self):
        with patch("bot.state.set_calendar_channel", return_value="123456789"):
            result = calendar.set_calendar_channel("123456789")
            assert result == "123456789"
            assert calendar.get_calendar_channel() == "123456789"

    def test_rejects_non_string(self):
        with patch("bot.state.set_calendar_channel", return_value=None):
            with pytest.raises(ValueError, match="valid Discord channel ID"):
                calendar.set_calendar_channel(123456789)

    def test_rejects_non_digits(self):
        with patch("bot.state.set_calendar_channel", return_value=None):
            with pytest.raises(ValueError, match="valid Discord channel ID"):
                calendar.set_calendar_channel("abc123")

    def test_allows_none_to_disable(self):
        with patch("bot.state.set_calendar_channel", return_value=None), \
             patch.object(calendar, "_schedule_old_message_deletion"):
            result = calendar.set_calendar_channel(None)
            assert result is None
            assert calendar.get_calendar_channel() is None

    def test_does_not_delete_on_same_channel(self):
        with patch("bot.state.set_calendar_channel", return_value="111111111"), \
             patch.object(calendar, "_schedule_old_message_deletion"):
            calendar.set_calendar_channel("111111111")
            assert calendar.get_calendar_channel() == "111111111"

    def test_does_not_delete_on_first_setup(self):
        calendar._calendar_channel_id = None
        with patch("bot.state.set_calendar_channel", return_value="111111111"), \
             patch.object(calendar, "_schedule_old_message_deletion"):
            calendar.set_calendar_channel("111111111")
            assert calendar.get_calendar_channel() == "111111111"

    @pytest.mark.asyncio
    async def test_resets_message_id_on_channel_change(self):
        calendar._calendar_channel_id = "111111111"
        calendar._calendar_message_id = "old_message_id"
        with patch("bot.state.set_calendar_channel", return_value="999999999"), \
             patch("bot.state.set_calendar_message_id"), \
             patch.object(calendar, "_delete_message", new_callable=AsyncMock) as mock_delete:
            calendar.set_calendar_channel("999999999")
            assert calendar.get_calendar_channel() == "999999999"
            assert calendar._calendar_message_id is None
            mock_delete.assert_called_once_with("111111111", "old_message_id")


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
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
            embed = calendar.build_calendar_embed()
            assert embed["description"] == "Calendrier des raids APT"

    def test_embed_highlights_today(self):
        today = get_today_date_string()
        with patch("bot.dates.get_raid_dates_snapshot", return_value=[today]):
            embed = calendar.build_calendar_embed()
            # First field is "Prochaine session", second is separator, third is the date
            assert "Prochaine session" in embed["fields"][0]["name"]
            assert "Dates" in embed["fields"][1]["name"]
            assert "*(aujourd'hui)*" in embed["fields"][2]["name"]
            assert "Calendar" in embed["fields"][2]["value"]

    def test_embed_has_color(self):
        calendar._calendar_color = 0xFF0000
        try:
            with patch("bot.dates.get_raid_dates_snapshot", return_value=[]):
                embed = calendar.build_calendar_embed()
                assert embed["color"] == 0xFF0000
        finally:
            calendar._calendar_color = 0x3B82F6

    def test_embed_has_footer(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
            embed = calendar.build_calendar_embed()
            assert "footer" in embed
            assert "text" in embed["footer"]
            assert "Mis a jour le" in embed["footer"]["text"]

    def test_embed_no_dates_message(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=[]):
            embed = calendar.build_calendar_embed()
            assert embed["description"] == "Aucune date de raid enregistree."
            assert "fields" not in embed

    def test_embed_sorted_dates(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["22/05/26", "15/05/26"]):
            embed = calendar.build_calendar_embed()
            # First field is "Prochaine session", second is separator, dates start at index 2
            assert "Prochaine session" in embed["fields"][0]["name"]
            assert "Dates" in embed["fields"][1]["name"]
            assert "Vendredi 15 Mai" in embed["fields"][2]["name"]
            assert "Vendredi 22 Mai" in embed["fields"][3]["name"]

    def test_embed_first_field_not_inline(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
            embed = calendar.build_calendar_embed()
            # First field (Prochaine session) is not inline
            assert embed["fields"][0]["inline"] is False
            # Second field (Dates separator) is not inline
            assert embed["fields"][1]["inline"] is False
            # Third field (date) is inline
            assert embed["fields"][2]["inline"] is True

    def test_embed_first_field_is_next_session(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
            embed = calendar.build_calendar_embed()
            assert "Prochaine session" in embed["fields"][0]["name"]
            assert embed["fields"][0]["inline"] is False
            # Value should be a Discord timestamp format
            assert embed["fields"][0]["value"].startswith("<t:")
            assert embed["fields"][0]["value"].endswith(":R>")

    def test_embed_has_thumbnail_when_configured(self):
        calendar._calendar_thumbnail_url = "https://example.com/thumb.png"
        try:
            with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
                embed = calendar.build_calendar_embed()
                assert "thumbnail" in embed
                assert embed["thumbnail"]["url"] == "https://example.com/thumb.png"
        finally:
            calendar._calendar_thumbnail_url = ""

    def test_embed_has_no_image_when_empty(self):
        calendar._calendar_image_url = ""
        try:
            with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
                embed = calendar.build_calendar_embed()
                assert "image" not in embed
        finally:
            calendar._calendar_image_url = ""

    def test_embed_has_no_thumbnail_when_empty(self):
        calendar._calendar_thumbnail_url = ""
        try:
            with patch("bot.dates.get_raid_dates_snapshot", return_value=["15/05/26"]):
                embed = calendar.build_calendar_embed()
                assert "thumbnail" not in embed
        finally:
            calendar._calendar_thumbnail_url = ""


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


class TestParseRaidDatetime:
    """Tests for _parse_raid_datetime."""

    def test_parses_summer_date(self):
        # 3 sept 2026 = été (UTC+2)
        result = calendar._parse_raid_datetime("03/09/26")
        assert result is not None
        start_utc, end_utc = result
        # 21h00 Paris été = 19h00 UTC
        assert start_utc.hour == 19
        assert start_utc.minute == 0
        # 23h59 Paris été = 21h59 UTC
        assert end_utc.hour == 21
        assert end_utc.minute == 59

    def test_parses_winter_date(self):
        # 7 jan 2026 = hiver (UTC+1)
        result = calendar._parse_raid_datetime("07/01/26")
        assert result is not None
        start_utc, end_utc = result
        # 21h00 Paris hiver = 20h00 UTC
        assert start_utc.hour == 20
        assert start_utc.minute == 0
        # 23h59 Paris hiver = 22h59 UTC
        assert end_utc.hour == 22
        assert end_utc.minute == 59

    def test_rejects_invalid_date(self):
        result = calendar._parse_raid_datetime("invalid")
        assert result is None

    def test_rejects_missing_date(self):
        result = calendar._parse_raid_datetime("")
        assert result is None


class TestBuildGcalLink:
    """Tests for build_gcal_link."""

    def test_builds_valid_link(self):
        link = calendar.build_gcal_link("03/09/26")
        assert link is not None
        assert "calendar.google.com" in link
        assert "action=TEMPLATE" in link
        assert "text=raid+APT" in link
        assert "location=Eorzea" in link
        assert "20260903T190000Z/20260903T215900Z" in link

    def test_builds_valid_link_winter(self):
        link = calendar.build_gcal_link("07/01/26")
        assert link is not None
        assert "20260107T200000Z/20260107T225900Z" in link

    def test_returns_none_for_invalid_date(self):
        link = calendar.build_gcal_link("invalid")
        assert link is None


class TestBuildDatesListWithGcal:
    """Tests for _build_dates_list with GCal links."""

    def test_includes_gcal_links(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["03/09/26", "07/01/26"]):
            embed = calendar.build_calendar_embed()
            # 1 "Prochaine session" + 1 separator + 2 dates = 4 fields
            assert len(embed["fields"]) == 4
            # First field is "Prochaine session"
            assert "Prochaine session" in embed["fields"][0]["name"]
            # Second field is separator
            assert "Dates" in embed["fields"][1]["name"]
            # Remaining fields contain the dates
            all_names = [f["name"] for f in embed["fields"][2:]]
            assert any("Jeudi 3 Sept." in n for n in all_names)
            assert any("Mercredi 7 Janv." in n for n in all_names)
            assert "Calendar" in embed["fields"][2]["value"]

    def test_includes_gcal_link_for_today(self):
        today = get_today_date_string()
        with patch("bot.dates.get_raid_dates_snapshot", return_value=[today]):
            embed = calendar.build_calendar_embed()
            # First field is "Prochaine session", second is separator, third is the date
            assert "Prochaine session" in embed["fields"][0]["name"]
            assert "Dates" in embed["fields"][1]["name"]
            assert "*(aujourd'hui)*" in embed["fields"][2]["name"]
            assert "Calendar" in embed["fields"][2]["value"]

    def test_embed_fields_inline_multiple(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["03/09/26", "07/01/26"]):
            embed = calendar.build_calendar_embed()
            # First field (Prochaine session) is not inline
            assert embed["fields"][0]["inline"] is False
            # Second field (Dates separator) is not inline
            assert embed["fields"][1]["inline"] is False
            # Remaining fields (dates) are inline
            for field in embed["fields"][2:]:
                assert field["inline"] is True

    def test_filters_invalid_dates(self):
        with patch("bot.dates.get_raid_dates_snapshot", return_value=["invalid"]):
            result = calendar._build_dates_list()
            # Invalid dates are silently filtered out
            assert result == "Aucune date de raid enregistree."



