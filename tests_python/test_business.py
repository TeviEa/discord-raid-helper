"""Tests for business logic coordinator."""

from unittest.mock import AsyncMock, patch

import pytest

from bot import business


class TestScheduleCalendarUpdate:
    """Tests for _schedule_calendar_update."""

    @pytest.mark.asyncio
    async def test_schedules_task_on_first_call(self):
        with patch.object(business.calendar, "update_calendar_message", new_callable=AsyncMock):
            business._schedule_calendar_update()
            assert business._calendar_update_task is not None
            assert not business._calendar_update_task.done()

    @pytest.mark.asyncio
    async def test_does_not_schedule_duplicate_task(self):
        mock_task = AsyncMock()
        mock_task.done = lambda: False

        with patch.object(business.calendar, "update_calendar_message", new_callable=AsyncMock):
            business._calendar_update_task = mock_task
            business._schedule_calendar_update()
            # Should still be the same task, not a new one
            assert business._calendar_update_task is mock_task


class TestSaveRaidDatesTriggersCalendarUpdate:
    """Tests that save_raid_dates triggers calendar update."""

    @pytest.mark.asyncio
    async def test_schedules_calendar_update(self):
        with patch("bot.business._cleanup_past_dates_and_persist"), \
             patch("bot.dates.save_raid_dates"), \
             patch("bot.state.set_dates"), \
             patch.object(business.calendar, "update_calendar_message", new_callable=AsyncMock) as mock_update:
            business.save_raid_dates("15/05/26")
            # The update task should have been scheduled
            assert business._calendar_update_task is not None


class TestDeleteRaidDatesTriggersCalendarUpdate:
    """Tests that delete_raid_dates triggers calendar update."""

    @pytest.mark.asyncio
    async def test_schedules_calendar_update(self):
        with patch("bot.business._cleanup_past_dates_and_persist"), \
             patch("bot.dates.delete_raid_dates"), \
             patch("bot.state.set_dates"), \
             patch.object(business.calendar, "update_calendar_message", new_callable=AsyncMock) as mock_update:
            business.delete_raid_dates("15/05/26")
            # The update task should have been scheduled
            assert business._calendar_update_task is not None


class TestDailyCheck:
    """Tests for daily_check business function."""

    def test_cleans_past_dates(self):
        with patch("bot.business._cleanup_past_dates_and_persist") as mock_cleanup:
            with patch.object(business.dates, "has_raid_date", return_value=True):
                business.daily_check()
                mock_cleanup.assert_called_once()

    def test_returns_true_when_today_is_raid_date(self):
        with patch("bot.business._cleanup_past_dates_and_persist"), \
             patch.object(business.dates, "has_raid_date", return_value=True):
            result = business.daily_check()
            assert result is True

    def test_returns_false_when_today_is_not_raid_date(self):
        with patch("bot.business._cleanup_past_dates_and_persist"), \
             patch.object(business.dates, "has_raid_date", return_value=False):
            result = business.daily_check()
            assert result is False
