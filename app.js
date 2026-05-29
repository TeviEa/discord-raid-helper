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
  markDateReminderSent,
  getRaidDatesSnapshot,
} from './raid-helper.js';

// Create an express app
const app = express();
// Get port, or default to 3333
const PORT = process.env.PORT || 3333;
const REMINDER_CHECK_INTERVAL_MS = 3333;
let reminderLoopRunning = false;

async function sendDueDateReminders() {
  if (reminderLoopRunning) {
    return;
  }

  reminderLoopRunning = true;
  try {
    const dueReminders = getDueDateReminders();

    for (const reminder of dueReminders) {
      await DiscordRequest(`channels/${reminder.channelId}/messages`, {
        method: 'POST',
        body: {
          content: formatDatesReminderMessage(reminder.date),
        },
      });

      markDateReminderSent(reminder.date, reminder.channelId);
    }
  } catch (error) {
    console.error('Error while sending date reminders', error);
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
              content: displayRaidDates(),
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
              content: displayRaidDates(),
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

    console.error(`unknown command: ${name}`);
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

    console.error('Autocomplete not implemented for', { name, subcommandName });
    return res.send({
      type: 8,
      data: { choices: [] },
    });
  }

  console.error('unknown interaction type', type);
  return res.status(400).json({ error: 'unknown interaction type' });
});

app.listen(PORT, () => {
  console.log('Listening on port', PORT);
});

setInterval(sendDueDateReminders, REMINDER_CHECK_INTERVAL_MS);
