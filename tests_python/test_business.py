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
             patch("bot.storage.write_dates_to_file"), \
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
             patch("bot.storage.write_dates_to_file"), \
             patch.object(business.calendar, "update_calendar_message", new_callable=AsyncMock) as mock_update:
            business.delete_raid_dates("15/05/26")
            # The update task should have been scheduled
            assert business._calendar_update_task is not None


class TestSetCalendarTitleTriggersUpdate:
    """Tests that set_calendar_title triggers a calendar update."""

    @pytest.mark.asyncio
    async def test_schedules_calendar_update(self):
        with patch.object(business.calendar, "set_calendar_title", return_value="New template"):
            with patch.object(business.calendar, "update_calendar_message", new_callable=AsyncMock):
                result = business.set_calendar_message("New template")
                assert result == "New template"
                assert business._calendar_update_task is not None
