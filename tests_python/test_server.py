"""Tests for server interaction handlers."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from bot import server, poll


class TestPollSendCommand:
    """Tests for /poll send command."""

    @pytest.mark.asyncio
    async def test_sends_poll(self):
        with patch("bot.business.post_poll_message", new_callable=AsyncMock, return_value={"channel_id": "123", "message_id": "msg123"}):
            body = {
                "type": 2,
                "data": {
                    "name": "poll",
                    "options": [{"name": "send", "options": []}],
                },
            }

            result = await server.handle_interaction(body)

            assert result["type"] == 4  # CHANNEL_MESSAGE_WITH_SOURCE
            assert "Sondage poste" in result["data"]["content"]

    @pytest.mark.asyncio
    async def test_fails_without_config(self):
        with patch("bot.business.post_poll_message", new_callable=AsyncMock, return_value=None):
            body = {
                "type": 2,
                "data": {
                    "name": "poll",
                    "options": [{"name": "send", "options": []}],
                },
            }

            result = await server.handle_interaction(body)

            assert result["type"] == 4
            assert "non configure" in result["data"]["content"]


class TestPollPingCommand:
    """Tests for /poll ping command."""

    @pytest.mark.asyncio
    async def test_sets_ping_role(self):
        with patch("bot.business.set_poll_ping_role", return_value="987654321"):
            body = {
                "type": 2,
                "data": {
                    "name": "poll",
                    "options": [{"name": "ping", "options": [{"name": "role", "value": 987654321}]}],
                },
            }

            result = await server.handle_interaction(body)

            assert result["type"] == 4
            assert "configure" in result["data"]["content"]

    @pytest.mark.asyncio
    async def test_clears_ping_role(self):
        with patch("bot.business.set_poll_ping_role", return_value=None):
            body = {
                "type": 2,
                "data": {
                    "name": "poll",
                    "options": [{"name": "ping", "options": []}],
                },
            }

            result = await server.handle_interaction(body)

            assert result["type"] == 4
            assert "desactive" in result["data"]["content"]


class TestPollShowCommand:
    """Tests for /poll show command."""

    @pytest.mark.asyncio
    async def test_shows_ping_role(self):
        with patch("bot.business.get_poll_day", return_value="tuesday"), \
             patch("bot.business.get_poll_channel", return_value="123"), \
             patch("bot.business.get_poll_message", return_value="Test"), \
             patch("bot.business.get_poll_pause", return_value=False), \
             patch("bot.business.get_poll_pause_until", return_value=""), \
             patch("bot.business.get_poll_ping_role", return_value="987654321"):
            body = {
                "type": 2,
                "data": {
                    "name": "poll",
                    "options": [{"name": "show", "options": []}],
                },
            }

            result = await server.handle_interaction(body)

            assert result["type"] == 4
            assert "ping role" in result["data"]["content"]
            assert "987654321" in result["data"]["content"]


class TestSendPollIfTodayIsConfigured:
    """Tests for send_poll_if_today_is_configured()."""

    @pytest.mark.asyncio
    async def test_sends_poll_on_configured_day_before_time(self):
        with patch("bot.server.dates.get_today_date_string", return_value="18/08/26"), \
             patch("bot.poll._poll_day", "tuesday"), \
             patch("bot.poll._poll_channel_id", "123456789"), \
             patch("bot.poll._poll_pause_enabled", False), \
             patch("bot.poll.post_poll_message", new_callable=AsyncMock, return_value={"channel_id": "123456789", "message_id": "msg123"}), \
             patch("bot.server.datetime") as mock_datetime, \
             patch("bot.server.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # Set up datetime to be before poll time
            mock_datetime.now.return_value = datetime(2026, 8, 18, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = await server.send_poll_if_today_is_configured()

            assert result is True
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_poll_on_configured_day_after_time(self):
        with patch("bot.server.dates.get_today_date_string", return_value="18/08/26"), \
             patch("bot.poll._poll_day", "tuesday"), \
             patch("bot.poll._poll_channel_id", "123456789"), \
             patch("bot.poll._poll_pause_enabled", False), \
             patch("bot.poll.post_poll_message", new_callable=AsyncMock) as mock_post, \
             patch("bot.server.datetime") as mock_datetime:
            # Set up datetime to be after poll time (21:00)
            mock_datetime.now.return_value = datetime(2026, 8, 18, 22, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = await server.send_poll_if_today_is_configured()

            assert result is False
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_poll_on_wrong_day(self):
        with patch("bot.server.dates.get_today_date_string", return_value="19/08/26"), \
             patch("bot.poll._poll_day", "tuesday"), \
             patch("bot.poll._poll_channel_id", "123456789"), \
             patch("bot.poll._poll_pause_enabled", False), \
             patch("bot.poll.post_poll_message", new_callable=AsyncMock) as mock_post, \
             patch("bot.server.datetime") as mock_datetime:
            # Wednesday (weekday 2) when poll day is Tuesday (weekday 1)
            mock_datetime.now.return_value = datetime(2026, 8, 19, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = await server.send_poll_if_today_is_configured()

            assert result is False
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_poll_when_paused(self):
        with patch("bot.server.dates.get_today_date_string", return_value="18/08/26"), \
             patch("bot.poll._poll_day", "tuesday"), \
             patch("bot.poll._poll_channel_id", "123456789"), \
             patch("bot.poll._poll_pause_enabled", True), \
             patch("bot.poll.post_poll_message", new_callable=AsyncMock) as mock_post, \
             patch("bot.server.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 8, 18, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = await server.send_poll_if_today_is_configured()

            assert result is False
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_poll_when_no_channel(self):
        with patch("bot.server.dates.get_today_date_string", return_value="18/08/26"), \
             patch("bot.poll._poll_day", "tuesday"), \
             patch("bot.poll._poll_channel_id", None), \
             patch("bot.poll._poll_pause_enabled", False), \
             patch("bot.poll.post_poll_message", new_callable=AsyncMock) as mock_post, \
             patch("bot.server.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 8, 18, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = await server.send_poll_if_today_is_configured()

            assert result is False
            mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_poll_when_no_day_configured(self):
        with patch("bot.server.dates.get_today_date_string", return_value="18/08/26"), \
             patch("bot.poll._poll_day", ""), \
             patch("bot.poll._poll_channel_id", "123456789"), \
             patch("bot.poll._poll_pause_enabled", False), \
             patch("bot.poll.post_poll_message", new_callable=AsyncMock) as mock_post, \
             patch("bot.server.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2026, 8, 18, 10, 0, 0)
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            result = await server.send_poll_if_today_is_configured()

            assert result is False
            mock_post.assert_not_called()
