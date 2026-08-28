"""Slash command definitions."""

DATES_COMMAND = {
    "name": "dates",
    "description": "Gestion des dates de raid",
    "options": [
        {
            "type": 1,  # Subcommand
            "name": "add",
            "description": "Ajoute les prochaines dates de raid",
            "options": [
                {
                    "type": 3,  # String
                    "name": "dates",
                    "description": "Dates de raid au format jj/mm/aa (separees par des virgules)",
                    "required": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "list",
            "description": "Affiche les prochaines dates de raid",
        },
        {
            "type": 1,  # Subcommand
            "name": "delete",
            "description": "Supprime des dates de raid",
            "options": [
                {
                    "type": 3,  # String
                    "name": "dates",
                    "description": "Dates de raid a supprimer au format jj/mm/aa",
                    "required": True,
                    "autocomplete": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "max",
            "description": "Definit le nombre maximum de dates affichees",
            "options": [
                {
                    "type": 4,  # Integer
                    "name": "max",
                    "description": "Nombre maximum de dates a afficher (>= 1)",
                    "required": True,
                },
            ],
        },
    ],
    "type": 1,  # SubcommandGroup
    "integration_types": [0, 1],
    "contexts": [0, 1, 2],
}

REMINDER_COMMAND = {
    "name": "reminder",
    "description": "Gestion des rappels de raid",
    "options": [
        {
            "type": 1,  # Subcommand
            "name": "channel",
            "description": "Definit le channel de rappel",
            "options": [
                {
                    "type": 7,  # Channel
                    "name": "channel",
                    "description": "Channel de rappel",
                    "required": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "message",
            "description": "Definit le message de rappel",
            "options": [
                {
                    "type": 3,  # String
                    "name": "message",
                    "description": "Message de rappel ({date} pour inserer la date)",
                    "required": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "show",
            "description": "Affiche la configuration actuelle du rappel",
        },
    ],
    "type": 1,  # SubcommandGroup
    "integration_types": [0, 1],
    "contexts": [0, 1, 2],
}

CALENDAR_COMMAND = {
    "name": "calendar",
    "description": "Gestion du calendrier de raids",
    "options": [
        {
            "type": 1,  # Subcommand
            "name": "channel",
            "description": "Definit le channel ou poster le calendrier",
            "options": [
                {
                    "type": 7,  # Channel
                    "name": "channel",
                    "description": "Channel pour le calendrier",
                    "required": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "delete",
            "description": "Supprime le message du calendrier actuel",
        },
    ],
    "type": 1,  # SubcommandGroup
    "integration_types": [0, 1],
    "contexts": [0, 1, 2],
}

DAY_CHOICES = [
    {"name": "Monday", "value": "monday"},
    {"name": "Tuesday", "value": "tuesday"},
    {"name": "Wednesday", "value": "wednesday"},
    {"name": "Thursday", "value": "thursday"},
    {"name": "Friday", "value": "friday"},
    {"name": "Saturday", "value": "saturday"},
    {"name": "Sunday", "value": "sunday"},
]

PAUSE_CHOICES = [
    {"name": "On", "value": "on"},
    {"name": "Off", "value": "off"},
]

POLL_COMMAND = {
    "name": "poll",
    "description": "Gestion du sondage de raid hebdomadaire",
    "options": [
        {
            "type": 1,  # Subcommand
            "name": "day",
            "description": "Definit le jour de la semaine du sondage",
            "options": [
                {
                    "type": 3,  # String
                    "name": "day",
                    "description": "Jour de la semaine (Mon, Tue, ...)",
                    "required": True,
                    "autocomplete": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "pause",
            "description": "Pause ou reprise du sondage",
            "options": [
                {
                    "type": 3,  # String
                    "name": "state",
                    "description": "On ou Off",
                    "required": True,
                    "autocomplete": True,
                },
                {
                    "type": 3,  # String
                    "name": "until",
                    "description": "Date de fin de pause (dd/mm/yy) ou vide",
                    "required": False,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "channel",
            "description": "Definit le channel du sondage",
            "options": [
                {
                    "type": 7,  # Channel
                    "name": "channel",
                    "description": "Channel du sondage",
                    "required": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "show",
            "description": "Affiche la configuration actuelle du sondage",
        },
        {
            "type": 1,  # Subcommand
            "name": "send",
            "description": "Envoie le sondage maintenant (pour tests)",
        },
        {
            "type": 1,  # Subcommand
            "name": "ping",
            "description": "Definit le role a mentionner apres le sondage",
            "options": [
                {
                    "type": 8,  # Role
                    "name": "role",
                    "description": "Role a mentionner (vide pour desactiver)",
                    "required": False,
                },
            ],
        },
    ],
    "type": 1,  # SubcommandGroup
    "integration_types": [0, 1],
    "contexts": [0, 1, 2],
}

ALL_COMMANDS = [DATES_COMMAND, REMINDER_COMMAND, CALENDAR_COMMAND, POLL_COMMAND]
