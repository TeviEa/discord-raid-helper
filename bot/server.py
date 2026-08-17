"""HTTP server for Discord interactions."""

import asyncio
import json
import os
from datetime import datetime

from discord_interactions import InteractionResponseType, InteractionType, verify_key

from . import business, calendar, dates, discord_api, reminder
from .commands import ALL_COMMANDS

PORT = int(os.environ.get("PORT", 3333))
PUBLIC_KEY = os.environ.get("PUBLIC_KEY", "")
APP_ID = os.environ.get("APP_ID", "")

last_reminder_sent_key = None


def log(*args):
    print(f"{__import__('datetime').datetime.now().isoformat()} {' '.join(str(a) for a in args)}")


def error(*args):
    print(f"{__import__('datetime').datetime.now().isoformat()} ERROR {' '.join(str(a) for a in args)}")


async def send_reminder_if_today_is_raid() -> None:
    """If today is a raid date, wait until the reminder time and send the reminder."""
    from . import reminder

    today = dates.get_today_date_string()
    if not dates.has_raid_date(today):
        return

    reminder_time = reminder.get_dates_reminder_time()
    reminder_key = f"{today}@{reminder_time}"

    if reminder_key == last_reminder_sent_key:
        return

    # Calculate seconds until reminder time
    now = datetime.now()
    current_seconds = now.hour * 3600 + now.minute * 60 + now.second
    reminder_seconds = reminder.reminder_hour * 3600 + reminder.reminder_minute * 60

    if reminder_seconds > current_seconds:
        # Reminder time is still today
        wait_seconds = reminder_seconds - current_seconds
    else:
        # Reminder time has passed today, skip it
        log(f"[reminder] reminder time {reminder_time} has passed for {today}, skipping")
        return

    log(f"[reminder] waiting {wait_seconds:.0f}s for reminder at {reminder_time} for {today}")
    await asyncio.sleep(wait_seconds)

    # Send the reminder
    channel_id = reminder.reminder_channel_id
    if not channel_id:
        return

    try:
        await discord_api.discord_request(
            f"channels/{channel_id}/messages",
            method="POST",
            body={"content": reminder.format_dates_reminder_message(today)},
        )
        log(f"[reminder] sent for {today} to channel {channel_id}")
        last_reminder_sent_key = reminder_key
    except Exception as e:
        error("Error while sending reminder", e)


async def daily_check() -> None:
    """Run the daily check: cleanup past dates, update calendar, schedule reminder."""
    from . import dates, reminder

    log("[daily] running daily check")

    # 1. Cleanup past dates
    business._cleanup_past_dates_and_persist()

    # 2. Update calendar
    if calendar._calendar_channel_id:
        await calendar.update_calendar_message()
        log("[daily] calendar updated")

    # 3. If today is a raid date, schedule the reminder
    if dates.has_raid_date(dates.get_today_date_string()):
        await send_reminder_if_today_is_raid()
        log("[daily] reminder scheduled for today")
    else:
        log("[daily] today is not a raid date")


async def daily_check_loop() -> None:
    """Run the daily check loop: wait until midnight, then run daily_check()."""
    while True:
        now = datetime.now()
        # Wait until midnight
        seconds_until_midnight = (24 - now.hour) * 3600 - now.minute * 60 - now.second
        log(f"[daily] next check in {seconds_until_midnight:.0f}s")
        await asyncio.sleep(seconds_until_midnight)
        await daily_check()


async def handle_interaction(body: dict) -> dict:
    """Handle a Discord interaction and return the response."""
    global last_reminder_sent_key

    interaction_type = body.get("type")
    data = body.get("data", {})
    name = data.get("name", "")

    # PING verification
    if interaction_type == InteractionType.PING:
        return {"type": InteractionResponseType.PONG}

    # Slash command
    if interaction_type == InteractionType.APPLICATION_COMMAND:
        subcommand = data.get("options", [{}])[0]
        subcommand_name = subcommand.get("name", "")
        subcommand_options = subcommand.get("options", [])

        def get_sub_option(option_name):
            return next((o["value"] for o in subcommand_options if o["name"] == option_name), None)

        # --- /dates ---
        if name == "dates":
            if subcommand_name == "list":
                return {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {"content": business.display_raid_dates()},
                }

            if subcommand_name == "add":
                try:
                    dates_input = get_sub_option("dates")
                    if not dates_input:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /dates add dates: 15/05/26,22/05/26"},
                        }
                    business.save_raid_dates(dates_input)
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Ajout de {dates_input}"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "delete":
                try:
                    dates_input = get_sub_option("dates")
                    if not dates_input:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /dates delete dates: 15/05/26,22/05/26"},
                        }
                    business.delete_raid_dates(dates_input)
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Supression de {dates_input}"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "max":
                try:
                    max_value = get_sub_option("max")
                    if max_value is None:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /dates max max: 10"},
                        }
                    updated = business.set_dates_display_max(max_value)
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Nombre maximum de dates affichees: {updated}"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

        # --- /reminder ---
        if name == "reminder":
            if subcommand_name == "show":
                time = business.get_dates_reminder_time()
                channel = business.get_dates_reminder_channel()
                message = business.get_dates_reminder_message()
                channel_str = f"<#{channel}>" if channel else "non defini"
                return {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": f"Configuration du rappel :\n- heure : {time} UTC\n- salon : {channel_str}\n- message : {message}"
                    },
                }

            if subcommand_name == "time":
                try:
                    time_value = get_sub_option("time")
                    if not time_value:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /reminder time time: 18:00"},
                        }
                    updated = business.set_dates_reminder_time(time_value)
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Heure de rappel configuree: {updated} UTC"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "channel":
                try:
                    channel_value = get_sub_option("channel")
                    if not channel_value:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /reminder channel channel: #general"},
                        }
                    updated = business.set_dates_reminder_channel(str(channel_value))
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Channel de rappel configure: <#{updated}>"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "message":
                try:
                    message_value = get_sub_option("message")
                    if not message_value:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /reminder message message: Rappel raid aujourd'hui ({date})"},
                        }
                    updated = business.set_dates_reminder_message(message_value)
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Message de rappel configure: {updated}"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

        # --- /calendar ---
        if name == "calendar":
            if subcommand_name == "channel":
                try:
                    channel_value = get_sub_option("channel")
                    if not channel_value:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /calendar channel channel: #general"},
                        }
                    updated = business.set_calendar_channel(str(channel_value))
                    # Post the calendar message in the new channel
                    result = await business.post_calendar_message()
                    if result:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": f"Calendrier poste dans <#{updated}>"},
                        }
                    else:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": f"Calendrier configure pour <#{updated}>, mais echec de la publication"},
                        }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "title":
                try:
                    title_value = get_sub_option("title")
                    if not title_value:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /calendar title title: Calendrier des raids"},
                        }
                    updated = business.set_calendar_message(title_value)
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Titre du calendrier configure: {updated}"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "color":
                try:
                    color_value = get_sub_option("color")
                    if color_value is None:
                        return {
                            "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                            "data": {"content": "Utilisation: /calendar color color: 16711680"},
                        }
                    updated = business.set_calendar_color(int(color_value))
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Couleur du calendrier configuree: 0x{updated:06X}"},
                    }
                except ValueError as e:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": f"Erreur: {e}"},
                    }

            if subcommand_name == "delete":
                deleted = await business.delete_calendar_message()
                if deleted:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": "Calendrier supprime"},
                    }
                else:
                    return {
                        "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                        "data": {"content": "Aucun calendrier a supprimer"},
                    }

        error(f"unknown command: {name}")
        return {"error": "unknown command"}

    # Autocomplete
    if interaction_type == 4:  # INTERACTION_AUTOCOMPLETE
        subcommand = data.get("options", [{}])[0]
        subcommand_name = subcommand.get("name", "")
        focused = next((o for o in subcommand.get("options", []) if o.get("focused")), None)

        if name == "dates" and subcommand_name == "delete" and focused and focused["name"] == "dates":
            current_input = focused.get("value", "")
            all_dates = business.get_raid_dates_snapshot()
            filtered = [d for d in all_dates if current_input.lower() in d.lower()]
            return {
                "type": 8,
                "data": {
                    "choices": [{"name": d, "value": d} for d in filtered[:25]],
                },
            }

        error(f"Autocomplete not implemented for {{name: {name}, subcommand: {subcommand_name}}}")
        return {"type": 8, "data": {"choices": []}}

    error(f"unknown interaction type: {interaction_type}")
    return {"error": "unknown interaction type"}


async def start_reminder_loop():
    """Start the periodic reminder check."""
    while True:
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)
        await send_due_date_reminders()


async def register_commands():
    """Register slash commands with Discord."""
    if not APP_ID:
        return

    import time

    max_retries = 5
    for attempt in range(max_retries):
        try:
            await discord_api.install_global_commands(APP_ID, ALL_COMMANDS)
            log("Slash commands registered")
            return
        except Exception as e:
            if attempt == max_retries - 1:
                error("Failed to register commands after", max_retries, "attempts:", e)
                return
            # Exponential backoff: 2s, 4s, 8s, 16s
            wait = min(2 ** (attempt + 1), 30)
            error("Command registration failed (attempt", attempt + 1, "):", e, "retrying in", wait, "s")
            await asyncio.sleep(wait)


async def main():
    """Start the bot."""
    import uvicorn

    # Register commands on startup
    await register_commands()

    # Run daily check immediately (catches up if bot was down)
    asyncio.create_task(daily_check())

    # Start daily check loop in background
    asyncio.create_task(daily_check_loop())

    # Start HTTP server within the existing event loop
    log("Starting server on port", PORT)
    config = uvicorn.Config(_create_app(), host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        log("Server stopped")


def _create_app():
    """Create the FastAPI app."""
    from fastapi import FastAPI, Request, Response
    from fastapi.responses import JSONResponse

    app = FastAPI()

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/interactions")
    async def interactions(request: Request):
        raw_body = await request.body()
        body = json.loads(raw_body)

        # Verify the request signature
        if not verify_key(
            raw_body,
            request.headers.get("X-Signature-Ed25519", ""),
            request.headers.get("X-Signature-Timestamp", ""),
            PUBLIC_KEY,
        ):
            return Response(status_code=401)

        try:
            result = await handle_interaction(body)
            return JSONResponse(content=result)
        except Exception as e:
            error("Interaction handler error:", e)
            return JSONResponse(content={"error": str(e)}, status_code=500)

    return app


if __name__ == "__main__":
    asyncio.run(main())
