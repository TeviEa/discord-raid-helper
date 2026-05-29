import 'dotenv/config';
import { InstallGlobalCommands } from './utils.js';

const DATES_COMMAND = {
  name: 'dates',
  description: 'Gestion des dates de raid',
  options: [
    {
      type: 1,
      name: 'add',
      description: 'Ajoute les prochaines dates de raid',
      options: [
        {
          type: 3,
          name: 'dates',
          description: 'Dates de raid au format jj/mm/aa (separees par des virgules)',
          required: true,
        },
      ],
    },
    {
      type: 1,
      name: 'list',
      description: 'Affiche les prochaines dates de raid',
    },
    {
      type: 1,
      name: 'delete',
      description: 'Supprime des dates de raid',
      options: [
        {
          type: 3,
          name: 'dates',
          description: 'Dates de raid a supprimer au format jj/mm/aa',
          required: true,
          autocomplete: true,
        },
      ],
    },
    {
      type: 1,
      name: 'max',
      description: 'Definit le nombre maximum de dates affichées',
      options: [
        {
          type: 4,
          name: 'max',
          description: 'Nombre maximum de dates à afficher (>= 1)',
          required: true,
        },
      ],
    },
  ],
  type: 1,
  integration_types: [0, 1],
  contexts: [0, 1, 2],
};

const REMINDER_COMMAND = {
  name: 'reminder',
  description: 'Gestion des rappels de raid',
  options: [
    {
      type: 1,
      name: 'time',
      description: 'Définit l\'heure de rappel',
      options: [
        {
          type: 3,
          name: 'time',
          description: 'Heure de rappel au format HH:mm (24h)',
          required: true,
        },
      ],
    },
    {
      type: 1,
      name: 'channel',
      description: 'Définit le channel de rappel',
      options: [
        {
          type: 7,
          name: 'channel',
          description: 'Channel de rappel',
          required: true,
        },
      ],
    },
    {
      type: 1,
      name: 'message',
      description: 'Définit le message de rappel',
      options: [
        {
          type: 3,
          name: 'message',
          description: 'Message de rappel ({date} pour insérer la date)',
          required: true,
        },
      ],
    },
  ],
  type: 1,
  integration_types: [0, 1],
  contexts: [0, 1, 2],
};

const ALL_COMMANDS = [
  DATES_COMMAND,
  REMINDER_COMMAND,
];

InstallGlobalCommands(process.env.APP_ID, ALL_COMMANDS);
