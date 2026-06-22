import 'dotenv/config';
import express from 'express';
import {
  InteractionResponseType,
  InteractionType,
  verifyKeyMiddleware,
} from 'discord-interactions';
import { DiscordRequest } from './utils.js';
import {
  saveRaidDates,
  displayRaidDates,
  deleteRaidDates,
  setDatesDisplayMax,
  setDatesReminderTime,
  setDatesReminderChannel,
  setDatesReminderMessage,
  formatDatesReminderMessage,
  getDueDateReminders,
  getRaidDatesSnapshot,
  getDatesReminderTime,
  getDatesReminderChannel,
  getDatesReminderMessage,
} from './raid-helper.js';

// Create an express app
const app = express();
// Get port, or default to 3333
const PORT = process.env.PORT || 3333;
const REMINDER_CHECK_INTERVAL_MS = 3333;
let reminderLoopRunning = false;
let lastReminderSentKey = null;

function log(...args) {
  console.log(new Date().toISOString(), ...args);
}

function error(...args) {
  console.error(new Date().toISOString(), ...args);
}

app.get('/health', (req, res) => {
  res.status(200).json({ status: 'ok' });
});

async function sendDueDateReminders() {
  if (reminderLoopRunning) {
    return;
  }

  reminderLoopRunning = true;
  try {
    const dueReminders = getDueDateReminders();

    if (dueReminders.length === 0) {
      return;
    }

    const today = dueReminders[0].date;
    const reminderTime = getDatesReminderTime();
    const reminderKey = `${today}@${reminderTime}`;
    if (reminderKey === lastReminderSentKey) {
      return;
    }

    for (const reminder of dueReminders) {
      await DiscordRequest(`channels/${reminder.channelId}/messages`, {
        method: 'POST',
        body: {
          content: formatDatesReminderMessage(reminder.date),
        },
      });
      log(`[reminder] sent for ${reminder.date} to channel ${reminder.channelId}`);
    }

    lastReminderSentKey = reminderKey;
  } catch (error) {
    error('Error while sending date reminders', error);
  } finally {
    reminderLoopRunning = false;
  }
}

/**
 * Interactions endpoint URL where Discord will send HTTP requests
 * Parse request body and verifies incoming requests using discord-interactions package
 */
app.post('/interactions', verifyKeyMiddleware(process.env.PUBLIC_KEY), async function (req, res) {
  // Interaction id, type and data
  const { type, data } = req.body;

  /**
   * Handle verification requests
   */
  if (type === InteractionType.PING) {
    return res.send({ type: InteractionResponseType.PONG });
  }

  /**
   * Handle slash command requests
   * See https://discord.com/developers/docs/interactions/application-commands#slash-commands
   */
  if (type === InteractionType.APPLICATION_COMMAND) {
    const { name } = data;
    const subcommand = data.options?.[0];
    const subcommandName = subcommand?.name;
    const subcommandOptions = subcommand?.options || [];

    function getSubOptionValue(optionName) {
      return subcommandOptions.find((option) => option.name === optionName)?.value;
    }

    if (name === 'dates') {
      if (subcommandName === 'list') {
        return res.send({
          type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
          data: {
            content: displayRaidDates(),
          },
        });
      }

      if (subcommandName === 'add') {
        try {
          const datesInput = getSubOptionValue('dates');

          if (!datesInput) {
            return res.send({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: {
                content: 'Utilisation: /dates add dates: 15/05/26,22/05/26',
              },
            });
          }

          saveRaidDates(datesInput);

          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Ajout de ${datesInput}`,
            },
          });
        } catch (error) {
          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Erreur: ${error.message}`,
            },
          });
        }
      }

      if (subcommandName === 'delete') {
        try {
          const datesInput = getSubOptionValue('dates');

          if (!datesInput) {
            return res.send({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: {
                content: 'Utilisation: /dates delete dates: 15/05/26,22/05/26',
              },
            });
          }

          deleteRaidDates(datesInput);

          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Supression de ${datesInput}`,
            },
          });
        } catch (error) {
          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Erreur: ${error.message}`,
            },
          });
        }
      }

      if (subcommandName === 'max') {
        try {
          const maxValue = getSubOptionValue('max');

          if (maxValue === undefined) {
            return res.send({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: {
                content: 'Utilisation: /dates max max: 10',
              },
            });
          }

          const updatedMax = setDatesDisplayMax(maxValue);

          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Nombre maximum de dates affichees: ${updatedMax}`,
            },
          });
        } catch (error) {
          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Erreur: ${error.message}`,
            },
          });
        }
      }
    }

    if (name === 'reminder') {
      if (subcommandName === 'show') {
        const time = getDatesReminderTime();
        const channel = getDatesReminderChannel();
        const message = getDatesReminderMessage();

        return res.send({
          type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
          data: {
            content: `Configuration du rappel :\n- heure : ${time}\n- salon : ${channel ? `<#${channel}>` : 'non défini'}\n- message : ${message}`,
          },
        });
      }
      if (subcommandName === 'time') {
        try {
          const timeValue = getSubOptionValue('time');

          if (!timeValue) {
            return res.send({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: {
                content: 'Utilisation: /reminder time time: 18:00',
              },
            });
          }

          const updatedTime = setDatesReminderTime(timeValue);

          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Heure de rappel configuree: ${updatedTime}`,
            },
          });
        } catch (error) {
          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Erreur: ${error.message}`,
            },
          });
        }
      }

      if (subcommandName === 'channel') {
        try {
          const channelValue = getSubOptionValue('channel');

          if (!channelValue) {
            return res.send({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: {
                content: 'Utilisation: /reminder channel channel: #general',
              },
            });
          }

          const updatedChannelId = setDatesReminderChannel(channelValue);

          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Channel de rappel configure: <#${updatedChannelId}>`,
            },
          });
        } catch (error) {
          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Erreur: ${error.message}`,
            },
          });
        }
      }

      if (subcommandName === 'message') {
        try {
          const messageValue = getSubOptionValue('message');

          if (!messageValue) {
            return res.send({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: {
                content: 'Utilisation: /reminder message message: Rappel raid aujourd\'hui ({date})',
              },
            });
          }

          const updatedMessage = setDatesReminderMessage(messageValue);

          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Message de rappel configure: ${updatedMessage}`,
            },
          });
        } catch (error) {
          return res.send({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: {
              content: `Erreur: ${error.message}`,
            },
          });
        }
      }
    }

    error(`unknown command: ${name}`);
    return res.status(400).json({ error: 'unknown command' });
  }

  /**
   * Handle autocomplete requests
   */
  if (type === 4) {
    const { name } = data;
    const subcommand = data.options?.[0];
    const subcommandName = subcommand?.name;
    const focusedOption = subcommand?.options?.find((option) => option.focused);

    if (name === 'dates' && subcommandName === 'delete' && focusedOption?.name === 'dates') {
      const currentInput = focusedOption.value || '';
      const allDates = getRaidDatesSnapshot();
      
      // Filter dates based on user input
      const filteredDates = allDates.filter((date) =>
        date.toLowerCase().includes(currentInput.toLowerCase())
      );

      return res.send({
        type: 8,
        data: {
          choices: filteredDates.slice(0, 25).map((date) => ({
            name: date,
            value: date,
          })),
        },
      });
    }

    error('Autocomplete not implemented for', { name, subcommandName });
    return res.send({
      type: 8,
      data: { choices: [] },
    });
  }

  error('unknown interaction type', type);
  return res.status(400).json({ error: 'unknown interaction type' });
});

app.listen(PORT, () => {
  log('Listening on port', PORT);
});

setInterval(sendDueDateReminders, REMINDER_CHECK_INTERVAL_MS);
