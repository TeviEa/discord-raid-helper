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

ALL_COMMANDS = [DATES_COMMAND, REMINDER_COMMAND]
