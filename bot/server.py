"""HTTP server for Discord interactions."""

import asyncio
import json
import os

from discord_interactions import InteractionResponseType, InteractionType, verify_key

from . import business, discord_api
from .commands import ALL_COMMANDS

PORT = int(os.environ.get("PORT", 3333))
PUBLIC_KEY = os.environ.get("PUBLIC_KEY", "")
APP_ID = os.environ.get("APP_ID", "")
REMINDER_CHECK_INTERVAL = 3.333  # seconds

reminder_loop_running = False
last_reminder_sent_key = None


def log(*args):
    print(f"{__import__('datetime').datetime.now().isoformat()} {' '.join(str(a) for a in args)}")


def error(*args):
    print(f"{__import__('datetime').datetime.now().isoformat()} ERROR {' '.join(str(a) for a in args)}")


async def send_due_date_reminders():
    """Periodically check and send due reminders."""
    global reminder_loop_running, last_reminder_sent_key

    if reminder_loop_running:
        return

    reminder_loop_running = True
    try:
        due_reminders = business.get_due_date_reminders()

        if not due_reminders:
            return

        today = due_reminders[0]["date"]
        reminder_time = business.get_dates_reminder_time()
        reminder_key = f"{today}@{reminder_time}"

        if reminder_key == last_reminder_sent_key:
            return

        for reminder in due_reminders:
            await discord_api.discord_request(
                f"channels/{reminder['channelId']}/messages",
                method="POST",
                body={"content": business.format_dates_reminder_message(reminder["date"])},
            )
            log(f"[reminder] sent for {reminder['date']} to channel {reminder['channelId']}")

        last_reminder_sent_key = reminder_key
    except Exception as e:
        error("Error while sending date reminders", e)
    finally:
        reminder_loop_running = False


def handle_interaction(body: dict) -> dict:
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
                        "content": f"Configuration du rappel :\n- heure : {time}\n- salon : {channel_str}\n- message : {message}"
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

    # Start reminder loop in background
    reminder_task = asyncio.create_task(start_reminder_loop())

    # Start HTTP server within the existing event loop
    log("Starting server on port", PORT)
    config = uvicorn.Config(_create_app(), host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    try:
        await server.serve()
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass
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
            result = handle_interaction(body)
            return JSONResponse(content=result)
        except Exception as e:
            error("Interaction handler error:", e)
            return JSONResponse(content={"error": str(e)}, status_code=500)

    return app


if __name__ == "__main__":
    asyncio.run(main())
