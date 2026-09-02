"""Calendar feature: post and manage a calendar message showing raid dates."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from . import config, dates, state

# Import format_raid_date for display
format_raid_date = dates.format_raid_date

# Raid time configuration from config.json (static)
_RAID_TIME_STR = config.get("raid.time")
_RAID_END_TIME_STR = config.get("raid.endTime")

# Parse raid time into hour/minute
_RAID_HOUR, _RAID_MINUTE = map(int, _RAID_TIME_STR.split(":"))
_RAID_END_HOUR, _RAID_END_MINUTE = map(int, _RAID_END_TIME_STR.split(":"))

# Paris timezone for DST-aware conversions
PARIS = ZoneInfo("Europe/Paris")

# GCal event title and location
_GCAL_TITLE = "raid APT"
_GCAL_LOCATION = "Eorzea"

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
_calendar_image_url: str = config.get("calendar.imageUrl") or ""
_calendar_thumbnail_url: str = config.get("calendar.thumbnailUrl") or ""

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


def _parse_raid_datetime(date_str: str) -> tuple[datetime, datetime] | None:
    """Parse a raid date string (dd/mm/yy) and return (start_dt, end_dt) in UTC.

    Args:
        date_str: Date in dd/mm/yy format.

    Returns:
        Tuple of (start_utc, end_utc) datetimes, or None if parsing fails.
    """
    try:
        day, month, year = map(int, date_str.split("/"))
        year += 2000  # Convert 2-digit year

        # Create aware datetime in Paris timezone
        start_local = datetime(year, month, day, _RAID_HOUR, _RAID_MINUTE, tzinfo=PARIS)
        end_local = datetime(year, month, day, _RAID_END_HOUR, _RAID_END_MINUTE, tzinfo=PARIS)

        # Convert to UTC
        start_utc = start_local.astimezone(timezone.utc)
        end_utc = end_local.astimezone(timezone.utc)

        return start_utc, end_utc
    except (ValueError, IndexError):
        return None


def build_gcal_link(date_str: str) -> str | None:
    """Build a Google Calendar link for a raid date.

    Args:
        date_str: Date in dd/mm/yy format.

    Returns:
        GCal URL string, or None if date parsing fails.
    """
    parsed = _parse_raid_datetime(date_str)
    if parsed is None:
        return None

    start_utc, end_utc = parsed

    # Format dates for GCal: YYYYMMDDTHHmmssZ
    start_str = start_utc.strftime("%Y%m%dT%H%M%SZ")
    end_str = end_utc.strftime("%Y%m%dT%H%M%SZ")

    # Build URL (spaces replaced with + for query params)
    url = (
        f"https://calendar.google.com/calendar/render?action=TEMPLATE"
        f"&text={_GCAL_TITLE.replace(' ', '+')}"
        f"&dates={start_str}/{end_str}"
        f"&location={_GCAL_LOCATION.replace(' ', '+')}"
    )
    return url


def _build_dates_list(now: datetime | None = None) -> str:
    """Build the bullet-point list of raid dates for embed description.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        Formatted date list with today highlighted and GCal links.
    """
    now = now or datetime.now()
    today_str = dates.get_today_date_string(now)

    all_dates = dates.get_raid_dates_snapshot()
    if not all_dates:
        return "Aucune date de raid enregistree."

    # Sort dates (skip invalid dates)
    valid_dates = []
    for date in all_dates:
        try:
            valid_dates.append((date, dates.to_sortable_timestamp(date)))
        except (ValueError, IndexError):
            pass  # Skip invalid dates

    valid_dates.sort(key=lambda x: x[1])
    sorted_dates = [d[0] for d in valid_dates]

    if not sorted_dates:
        return "Aucune date de raid enregistree."

    # Build date list with blockquoted GCal links
    date_lines = []
    for date in sorted_dates:
        gcal_url = build_gcal_link(date)
        if date == today_str:
            date_lines.append(f"📅 **{date}** *(aujourd'hui)*")
        else:
            date_lines.append(f"📅 **{date}**")
        link = f"> 🗓️ [Google Calendar]({gcal_url})" if gcal_url else "> —"
        date_lines.append(link)
        date_lines.append("")  # blank line between dates
    return "\n".join(date_lines).rstrip()


def build_calendar_embed(now: datetime | None = None) -> dict:
    """Build the Discord embed payload for the calendar message.

    Args:
        now: Optional datetime for testing. Uses current time if not provided.

    Returns:
        Discord embed dict with title, description, fields, footer, image, and thumbnail.
    """
    now = now or datetime.now()
    today_str = dates.get_today_date_string(now)

    all_dates = dates.get_raid_dates_snapshot()
    if not all_dates:
        embed = {
            "title": _calendar_title,
            "description": "Aucune date de raid enregistree.",
            "color": _calendar_color,
            "footer": {
                "text": f"Mis a jour le {dates.get_today_date_string(now)}",
            },
        }
    else:
        # Sort dates (skip invalid dates)
        valid_dates = []
        for date in all_dates:
            try:
                valid_dates.append((date, dates.to_sortable_timestamp(date)))
            except (ValueError, IndexError):
                pass  # Skip invalid dates

        valid_dates.sort(key=lambda x: x[1])
        sorted_dates = [d[0] for d in valid_dates]

        # Build fields
        fields = []

        # First field: next session (relative time, full width)
        next_date = sorted_dates[0]
        fields.append({
            "name": "Prochaine session",
            "value": dates.format_discord_date_relative(next_date),
            "inline": False,
        })

        # Separator field
        fields.append({
            "name": "Dates",
            "value": "-------",
            "inline": False,
        })

        # Remaining fields: all dates (inline)
        for date in sorted_dates:
            gcal_url = build_gcal_link(date)
            formatted = format_raid_date(date)
            if date == today_str:
                name = f"🗓️ **{formatted}** *(aujourd'hui)*"
            else:
                name = f"🗓️ **{formatted}**"
            value = f"🌐 [Calendar]({gcal_url})" if gcal_url else "🗓️ —"
            fields.append({
                "name": name,
                "value": value,
                "inline": True,
            })

        embed = {
            "title": _calendar_title,
            "description": "Calendrier des raids APT",
            "fields": fields,
            "color": _calendar_color,
            "footer": {
                "text": f"Mis a jour le {dates.get_today_date_string(now)}",
            },
        }

    # Add image if configured
    if _calendar_image_url:
        embed["image"] = {"url": _calendar_image_url}

    # Add thumbnail if configured
    if _calendar_thumbnail_url:
        embed["thumbnail"] = {"url": _calendar_thumbnail_url}

    return embed


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






