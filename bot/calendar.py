"""Calendar feature: post and manage a calendar message showing raid dates."""

from datetime import datetime

from . import config, dates, state

__all__ = [
    "set_calendar_channel",
    "get_calendar_channel",
    "build_calendar_embed",
    "post_calendar_message",
    "delete_calendar_message",
    "update_calendar_message",
]

# Static config from config.json
_calendar_title: str = config.get("calendar.title")
_calendar_color: int = config.get("calendar.color")

# Dynamic state from state.json
_calendar_channel_id: str | None = None
_calendar_message_id: str | None = None


def set_calendar_channel(channel_id: str | None) -> str | None:
    """Set the calendar channel ID.

    Args:
        channel_id: Discord channel ID (digits only) or None to disable.

    Returns:
        The new channel ID or None.

    Raises:
        ValueError: If channel_id is not a valid Discord channel ID.
    """
    if channel_id is not None:
        if not isinstance(channel_id, str) or not channel_id.isdigit():
            raise ValueError("Calendar channel must be a valid Discord channel ID (digits only)")

    global _calendar_channel_id, _calendar_message_id
    old_channel = _calendar_channel_id
    old_message_id = _calendar_message_id
    _calendar_channel_id = channel_id
    _calendar_message_id = None  # Reset message ID when channel changes
    state.set_calendar_channel(channel_id)
    state.set_calendar_message_id(None)

    # Delete old message when channel changes (not on first setup)
    if old_channel is not None and old_channel != channel_id:
        _schedule_old_message_deletion(old_channel, old_message_id)

    return _calendar_channel_id


# Track pending deletions to avoid duplicates
_deletion_task = None


def _schedule_old_message_deletion(channel_id: str, message_id: str) -> None:
    """Schedule a background deletion of an old calendar message."""
    global _deletion_task
    if _deletion_task is not None and not _deletion_task.done():
        return
    import asyncio

    _deletion_task = asyncio.create_task(_delete_message(channel_id, message_id))


async def _delete_message(channel_id: str, message_id: str) -> None:
    """Delete a message from a channel."""
    from . import discord_api

    try:
        await discord_api.discord_request(
            f"channels/{channel_id}/messages/{message_id}",
            method="DELETE",
        )
    except Exception as e:
        print(f"[{__name__}] Failed to delete old calendar message: {e}")


def get_calendar_channel() -> str | None:
    """Get the current calendar channel ID."""
    return _calendar_channel_id


def _build_dates_list(now: datetime | None = None) -> str:
    """Build the bullet-point list of raid dates for embed description.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        Formatted date list with today highlighted.
    """
    now = now or datetime.now()
    today_str = dates.get_today_date_string(now)

    all_dates = dates.get_raid_dates_snapshot()
    if not all_dates:
        return "Aucune date de raid enregistree."

    # Sort dates
    sorted_dates = sorted(all_dates, key=dates.to_sortable_timestamp)

    # Build date list
    date_lines = []
    for date in sorted_dates:
        if date == today_str:
            date_lines.append(f"- **{date}** (aujourd'hui)")
        else:
            date_lines.append(f"- {date}")
    return "\n".join(date_lines)


def build_calendar_embed(now: datetime | None = None) -> dict:
    """Build the Discord embed payload for the calendar message.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        Discord embed dict with title, description, and footer.
    """
    now = now or datetime.now()
    date_list = _build_dates_list(now)

    return {
        "title": _calendar_title,
        "description": date_list,
        "color": _calendar_color,
        "footer": {
            "text": f"Mis a jour le {dates.get_today_date_string(now)}",
        },
    }


async def post_calendar_message() -> dict | None:
    """Post the calendar embed message in the configured channel.

    Returns:
        Dict with 'channel_id' and 'message_id' on success, or None on failure.
    """
    global _calendar_message_id

    from . import discord_api

    if not _calendar_channel_id:
        return None

    embed = build_calendar_embed()

    try:
        data = await discord_api.discord_request(
            f"channels/{_calendar_channel_id}/messages",
            method="POST",
            body={"embeds": [embed]},
        )
        _calendar_message_id = data.get("id")
        state.set_calendar_message_id(_calendar_message_id)
        return {"channel_id": _calendar_channel_id, "message_id": _calendar_message_id}
    except Exception as e:
        print(f"[{__name__}] Failed to post calendar message: {e}")
        return None


async def delete_calendar_message() -> bool:
    """Delete the current calendar message.

    Returns:
        True if deleted successfully, False otherwise.
    """
    global _calendar_message_id

    from . import discord_api

    if not _calendar_channel_id or not _calendar_message_id:
        return False

    try:
        await discord_api.discord_request(
            f"channels/{_calendar_channel_id}/messages/{_calendar_message_id}",
            method="DELETE",
        )
        _calendar_message_id = None
        state.set_calendar_message_id(None)
        return True
    except Exception as e:
        print(f"[{__name__}] Failed to delete calendar message: {e}")
        return False


async def update_calendar_message() -> dict | None:
    """Update the calendar embed in place, or post a new one if it doesn't exist.

    Returns:
        Dict with 'channel_id' and 'message_id' on success, or None on failure.
    """
    from . import discord_api

    if not _calendar_channel_id:
        return None

    embed = build_calendar_embed()

    try:
        if _calendar_message_id:
            # Edit existing message
            data = await discord_api.discord_request(
                f"channels/{_calendar_channel_id}/messages/{_calendar_message_id}",
                method="PATCH",
                body={"embeds": [embed]},
            )
            return {"channel_id": _calendar_channel_id, "message_id": data.get("id")}
        else:
            # Post new message
            return await post_calendar_message()
    except Exception as e:
        print(f"[{__name__}] Failed to update calendar message: {e}")
        return None






