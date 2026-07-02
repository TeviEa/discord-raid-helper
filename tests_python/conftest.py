"""Pytest configuration for tests_python/."""

import pytest


pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(autouse=True)
def reset_calendar_state():
    """Reset calendar state before each test."""
    from bot import calendar

    original_channel = calendar._calendar_channel_id
    original_message_id = calendar._calendar_message_id
    original_title = calendar._calendar_title
    original_color = calendar._calendar_color
    original_deletion_task = calendar._deletion_task

    yield

    calendar._calendar_channel_id = original_channel
    calendar._calendar_message_id = original_message_id
    calendar._calendar_title = original_title
    calendar._calendar_color = original_color
    calendar._deletion_task = original_deletion_task


@pytest.fixture(autouse=True)
def reset_dates_state():
    """Reset dates state before each test."""
    from bot import dates

    original_dates = dates._dates_memory
    original_max = dates._display_max_dates

    yield

    dates._dates_memory = original_dates
    dates._display_max_dates = original_max


@pytest.fixture(autouse=True)
def reset_reminder_state():
    """Reset reminder state before each test."""
    from bot import reminder

    original_hour = reminder.reminder_hour
    original_minute = reminder.reminder_minute
    original_channel = reminder.reminder_channel_id
    original_message = reminder.reminder_message_template

    yield

    reminder.reminder_hour = original_hour
    reminder.reminder_minute = original_minute
    reminder.reminder_channel_id = original_channel
    reminder.reminder_message_template = original_message
