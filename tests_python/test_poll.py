"""Tests for poll feature using Discord native polls."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from bot import poll


class TestSetPollDay:
    """Tests for set_poll_day."""

    def test_sets_valid_day(self):
        result = poll.set_poll_day("tuesday")
        assert result == "tuesday"

    def test_sets_day_case_insensitive(self):
        result = poll.set_poll_day("TUESDAY")
        assert result == "tuesday"

    def test_rejects_invalid_day(self):
        with pytest.raises(ValueError):
            poll.set_poll_day("invalid")

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            poll.set_poll_day(123)


class TestGetPollDay:
    """Tests for get_poll_day."""

    def test_returns_configured_day(self):
        poll.set_poll_day("monday")
        assert poll.get_poll_day() == "monday"


class TestSetPollChannel:
    """Tests for set_poll_channel."""

    def test_sets_valid_channel(self):
        result = poll.set_poll_channel("123456789")
        assert result == "123456789"

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            poll.set_poll_channel(123)

    def test_rejects_non_digits(self):
        with pytest.raises(ValueError):
            poll.set_poll_channel("abc")

    def test_allows_none_to_disable(self):
        result = poll.set_poll_channel(None)
        assert result is None


class TestGetPollChannel:
    """Tests for get_poll_channel."""

    def test_returns_configured_channel(self):
        poll.set_poll_channel("123456789")
        assert poll.get_poll_channel() == "123456789"


class TestSetPollMessage:
    """Tests for set_poll_message (poll question)."""

    def test_sets_valid_message(self):
        result = poll.set_poll_message("Qui est dispo ?")
        assert result == "Qui est dispo ?"

    def test_trims_whitespace(self):
        result = poll.set_poll_message("  Qui est dispo ?  ")
        assert result == "Qui est dispo ?"

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            poll.set_poll_message("")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError):
            poll.set_poll_message("   ")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError):
            poll.set_poll_message("x" * 201)

    def test_accepts_max_length(self):
        result = poll.set_poll_message("x" * 200)
        assert result == "x" * 200


class TestGetPollMessage:
    """Tests for get_poll_message."""

    def test_returns_configured_message(self):
        poll.set_poll_message("Test message")
        assert poll.get_poll_message() == "Test message"


class TestSetPollPause:
    """Tests for set_poll_pause."""

    def test_enables_pause(self):
        result = poll.set_poll_pause(True)
        assert result is True

    def test_disables_pause(self):
        result = poll.set_poll_pause(False)
        assert result is False


class TestGetPollPause:
    """Tests for get_poll_pause."""

    def test_returns_configured_pause(self):
        poll.set_poll_pause(True)
        assert poll.get_poll_pause() is True


class TestSetPollPauseUntil:
    """Tests for set_poll_pause_until."""

    def test_sets_valid_date(self):
        result = poll.set_poll_pause_until("25/12/26")
        assert result == "25/12/26"

    def test_clears_empty(self):
        poll.set_poll_pause_until("25/12/26")
        result = poll.set_poll_pause_until("")
        assert result == ""

    def test_rejects_invalid_date(self):
        with pytest.raises(ValueError):
            poll.set_poll_pause_until("invalid")

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            poll.set_poll_pause_until(123)


class TestGetPollPauseUntil:
    """Tests for get_poll_pause_until."""

    def test_returns_configured_until(self):
        poll.set_poll_pause_until("25/12/26")
        assert poll.get_poll_pause_until() == "25/12/26"


class TestShouldSendPoll:
    """Tests for _should_send_poll."""

    def test_returns_true_when_configured(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_pause(False)

        now = datetime(2026, 8, 18, 21, 0, 0)  # Tuesday at 21:00
        assert poll._should_send_poll(now) is True

    def test_returns_false_when_paused(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_pause(True)

        now = datetime(2026, 8, 18, 21, 0, 0)
        assert poll._should_send_poll(now) is False

    def test_returns_false_when_not_configured_day(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_pause(False)

        now = datetime(2026, 8, 19, 21, 0, 0)  # Wednesday
        assert poll._should_send_poll(now) is False

    def test_returns_false_when_no_channel(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel(None)
        poll.set_poll_pause(False)

        now = datetime(2026, 8, 18, 10, 0, 0)  # Any time on Tuesday
        assert poll._should_send_poll(now) is False

    def test_returns_true_at_any_time_on_configured_day(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_pause(False)

        now = datetime(2026, 8, 18, 10, 30, 0)  # Tuesday at 10:30
        assert poll._should_send_poll(now) is True

    def test_lifts_pause_when_until_date_reached(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_pause(True)
        poll.set_poll_pause_until("18/08/26")  # Same day

        now = datetime(2026, 8, 18, 21, 0, 0)
        assert poll._should_send_poll(now) is True
        assert poll.get_poll_pause() is False  # Pause lifted


class TestGetPollDates:
    """Tests for _get_poll_dates."""

    def test_returns_dates_excluding_raid_days(self):
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)  # Tuesday
        dates = poll._get_poll_dates(now)
        # Should return 6 dates (7 days - 1 raid day)
        assert len(dates) == 7 - len(poll.RAID_DAYS)

    def test_dates_are_consecutive(self):
        # Temporarily clear RAID_DAYS for this test
        original_raid_days = poll.RAID_DAYS[:]
        poll.RAID_DAYS = []
        try:
            poll.set_poll_day("tuesday")
            now = datetime(2026, 8, 18, 21, 0, 0)
            dates = poll._get_poll_dates(now)
            for i in range(1, len(dates)):
                delta = (dates[i]["date_obj"] - dates[i-1]["date_obj"]).days
                assert delta == 1
        finally:
            poll.RAID_DAYS = original_raid_days

    def test_starts_next_week(self):
        poll.set_poll_day("tuesday")
        # Tuesday August 18, 2026
        now = datetime(2026, 8, 18, 21, 0, 0)
        dates = poll._get_poll_dates(now)
        # Should start on Wednesday (Aug 26) since Tuesday is excluded
        assert dates[0]["date_obj"].day == 26
        assert dates[0]["date_obj"].weekday() == 2  # Wednesday

    def test_includes_day_names(self):
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        dates = poll._get_poll_dates(now)
        for d in dates:
            assert "day_name" in d
            assert "day_short" in d
            assert "date_str" in d

    def test_excludes_raid_days(self):
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)  # Tuesday
        dates = poll._get_poll_dates(now)
        # Tuesday is weekday 1, should be excluded
        for d in dates:
            assert d["date_obj"].weekday() != 1, "Tuesday should be excluded from poll dates"


class TestBuildPollMessage:
    """Tests for build_poll_message (Discord native poll)."""

    def test_returns_dict(self):
        poll.set_poll_message("Qui est dispo ?")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        assert isinstance(body, dict)

    def test_includes_poll_structure(self):
        poll.set_poll_message("Qui est dispo ?")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        assert "poll" in body

    def test_includes_question(self):
        poll.set_poll_message("Qui est dispo ?")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        assert body["poll"]["question"]["text"] == "Qui est dispo ?"

    def test_has_correct_number_of_answers(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        # 7 days - RAID_DAYS + 1 "Je ne peux pas"
        expected_answers = 7 - len(poll.RAID_DAYS) + 1
        assert len(body["poll"]["answers"]) == expected_answers

    def test_answers_have_poll_media(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        for answer in body["poll"]["answers"]:
            assert "poll_media" in answer
            assert "text" in answer["poll_media"]
            assert "emoji" in answer["poll_media"]
            assert "name" in answer["poll_media"]["emoji"]

    def test_includes_day_options(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        answers = body["poll"]["answers"]
        # First N answers should be day names with dates (N = 7 - RAID_DAYS)
        day_options = len(answers) - 1  # Last one is "Je ne peux pas"
        for i in range(day_options):
            assert "poll_media" in answers[i]
            assert "text" in answers[i]["poll_media"]
            assert "emoji" in answers[i]["poll_media"]
            assert "name" in answers[i]["poll_media"]["emoji"]
            # Each day option text should have a short day name (3 chars) and a date
            day_text = answers[i]["poll_media"]["text"]
            assert len(day_text.split()[0]) == 3  # Short day name
            assert "/" in day_text  # Date format DD/MM

    def test_includes_not_available_option(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        answers = body["poll"]["answers"]
        # Last answer should be the "not available" option
        last_answer = answers[-1]
        assert "Pas de session bonus" in last_answer["poll_media"]["text"]
        assert "poll_media" in last_answer
        assert "emoji" in last_answer["poll_media"]
        assert last_answer["poll_media"]["emoji"]["name"] == "\u274c"  # ❌

    def test_allows_multiselect(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        assert body["poll"]["allow_multiselect"] is True

    def test_has_layout_type(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        assert body["poll"]["layout_type"] == 1

    def test_has_duration(self):
        poll.set_poll_message("Test")
        poll.set_poll_day("tuesday")
        now = datetime(2026, 8, 18, 21, 0, 0)
        body = poll.build_poll_message(now)
        assert body["poll"]["duration"] == poll._POLL_DURATION_HOURS


class TestPostPollMessage:
    """Tests for post_poll_message."""

    @pytest.mark.asyncio
    async def test_posts_poll_message(self):
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Qui est dispo ?")
        poll.set_poll_day("tuesday")

        with patch("bot.discord_api.discord_request", new_callable=AsyncMock, return_value={"id": "msg123"}) as mock_request:
            result = await poll.post_poll_message()
            assert result == {"channel_id": "123456789", "message_id": "msg123"}

            # Verify poll structure was sent
            call_args = mock_request.call_args
            body = call_args[1]["body"]
            assert "poll" in body
            assert body["poll"]["question"]["text"] == "Qui est dispo ?"
            # Expected: 7 days - RAID_DAYS + 1 "Je ne peux pas"
            expected_answers = 7 - len(poll.RAID_DAYS) + 1
            assert len(body["poll"]["answers"]) == expected_answers
            assert body["poll"]["allow_multiselect"] is True
            assert body["poll"]["layout_type"] == 1
            for answer in body["poll"]["answers"]:
                assert "poll_media" in answer
                assert "text" in answer["poll_media"]
                assert "emoji" in answer["poll_media"]
                assert "name" in answer["poll_media"]["emoji"]

    @pytest.mark.asyncio
    async def test_returns_none_without_channel(self):
        poll.set_poll_channel(None)
        poll.set_poll_message("Test")
        result = await poll.post_poll_message()
        assert result is None

    @pytest.mark.asyncio
    async def test_handles_api_error(self):
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")

        with patch("bot.discord_api.discord_request", new_callable=AsyncMock, side_effect=Exception("API error")):
            result = await poll.post_poll_message()
            assert result is None

    @pytest.mark.asyncio
    async def test_posts_ping_message_after_poll(self):
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_ping_role("987654321")

        with patch("bot.discord_api.discord_request", new_callable=AsyncMock, return_value={"id": "msg123"}) as mock_request:
            result = await poll.post_poll_message()
            assert result == {"channel_id": "123456789", "message_id": "msg123"}

            # Verify two calls were made: poll + ping
            assert mock_request.call_count == 2

            # First call: poll message
            first_call = mock_request.call_args_list[0]
            assert first_call[1]["method"] == "POST"
            assert "poll" in first_call[1]["body"]

            # Second call: ping message
            second_call = mock_request.call_args_list[1]
            assert second_call[1]["method"] == "POST"
            assert "<@&987654321>" in second_call[1]["body"]["content"]


class TestSetPollPingRole:
    """Tests for set_poll_ping_role."""

    def test_sets_valid_role(self):
        result = poll.set_poll_ping_role("987654321")
        assert result == "987654321"

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            poll.set_poll_ping_role(123)

    def test_rejects_non_digits(self):
        with pytest.raises(ValueError):
            poll.set_poll_ping_role("abc")

    def test_allows_none_to_disable(self):
        result = poll.set_poll_ping_role(None)
        assert result is None


class TestGetPollPingRole:
    """Tests for get_poll_ping_role."""

    def test_returns_configured_role(self):
        poll.set_poll_ping_role("987654321")
        assert poll.get_poll_ping_role() == "987654321"


class TestGetPollConfig:
    """Tests for get_poll_config."""

    def test_returns_full_config(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_pause(False)
        poll.set_poll_pause_until("")
        poll.set_poll_ping_role("987654321")

        config = poll.get_poll_config()
        assert config["day"] == "tuesday"
        assert config["channelId"] == "123456789"
        assert config["message"] == "Test"
        assert config["pause"]["enabled"] is False
        assert config["pause"]["until"] == ""
        assert config["pingRole"] == "987654321"

    def test_returns_none_ping_role(self):
        poll.set_poll_day("tuesday")
        poll.set_poll_channel("123456789")
        poll.set_poll_message("Test")
        poll.set_poll_pause(False)
        poll.set_poll_ping_role(None)

        config = poll.get_poll_config()
        assert config["pingRole"] is None
