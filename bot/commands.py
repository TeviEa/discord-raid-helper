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
            "name": "time",
            "description": "Definit l'heure de rappel (UTC)",
            "options": [
                {
                    "type": 3,  # String
                    "name": "time",
                    "description": "Heure de rappel au format HH:mm (24h) en UTC",
                    "required": True,
                },
            ],
        },
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
            "name": "title",
            "description": "Definit le titre du calendrier",
            "options": [
                {
                    "type": 3,  # String
                    "name": "title",
                    "description": "Titre du calendrier (max 256 caracteres)",
                    "required": True,
                },
            ],
        },
        {
            "type": 1,  # Subcommand
            "name": "color",
            "description": "Definit la couleur du calendrier",
            "options": [
                {
                    "type": 4,  # Integer
                    "name": "color",
                    "description": "Couleur hexadecimal (ex: 16711680 pour rouge)",
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

ALL_COMMANDS = [DATES_COMMAND, REMINDER_COMMAND, CALENDAR_COMMAND]
