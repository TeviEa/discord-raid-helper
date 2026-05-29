let reminderHour = 18;
let reminderMinute = 0;
let reminderChannelId = null;
let reminderMessageTemplate = 'Rappel raid: la date {date} est aujourd\'hui.';
const sentReminderKeys = new Set();

function getTodayDateString(now = new Date()) {
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const year = String(now.getFullYear() % 100).padStart(2, '0');
  return `${day}/${month}/${year}`;
}

export function setDatesReminderTime(timeInput) {
  if (typeof timeInput !== 'string') {
    throw new Error('Reminder time must be a string in HH:mm format');
  }

  const match = /^(\d{2}):(\d{2})$/.exec(timeInput.trim());
  if (!match) {
    throw new Error('Reminder time must be in HH:mm format');
  }

  const parsedHour = Number(match[1]);
  const parsedMinute = Number(match[2]);

  if (parsedHour < 0 || parsedHour > 23 || parsedMinute < 0 || parsedMinute > 59) {
    throw new Error('Reminder time must be a valid 24h time (HH:mm)');
  }

  reminderHour = parsedHour;
  reminderMinute = parsedMinute;

  return getDatesReminderTime();
}

export function getDatesReminderTime() {
  return `${String(reminderHour).padStart(2, '0')}:${String(reminderMinute).padStart(2, '0')}`;
}

export function setDatesReminderChannel(channelId) {
  if (typeof channelId !== 'string' || !/^\d+$/.test(channelId)) {
    throw new Error('Reminder channel must be a valid Discord channel id');
  }

  reminderChannelId = channelId;
  return reminderChannelId;
}

export function setDatesReminderMessage(messageInput) {
  if (typeof messageInput !== 'string') {
    throw new Error('Reminder message must be a string');
  }

  const trimmedMessage = messageInput.trim();
  if (trimmedMessage.length === 0) {
    throw new Error('Reminder message cannot be empty');
  }

  if (trimmedMessage.length > 2000) {
    throw new Error('Reminder message cannot exceed 2000 characters');
  }

  reminderMessageTemplate = trimmedMessage;
  return reminderMessageTemplate;
}

export function formatDatesReminderMessage(date) {
  return reminderMessageTemplate.replaceAll('{date}', date);
}

export function getDueDateReminders(hasDate, now = new Date()) {
  if (typeof hasDate !== 'function') {
    throw new TypeError('hasDate must be a function');
  }

  if (now.getHours() !== reminderHour || now.getMinutes() !== reminderMinute) {
    return [];
  }

  const todayDateString = getTodayDateString(now);
  if (!hasDate(todayDateString)) {
    return [];
  }

  const channels = reminderChannelId ? [reminderChannelId] : [];

  if (channels.length === 0) {
    return [];
  }

  const dueReminders = [];
  for (const channelId of channels) {
    const reminderKey = `${todayDateString}|${channelId}`;
    if (!sentReminderKeys.has(reminderKey)) {
      dueReminders.push({ date: todayDateString, channelId });
    }
  }

  return dueReminders;
}

export function markDateReminderSent(date, channelId) {
  sentReminderKeys.add(`${date}|${channelId}`);
}

export function clearSentRemindersForDates(dates) {
  if (!Array.isArray(dates) || dates.length === 0) {
    return;
  }

  for (const date of dates) {
    for (const reminderKey of sentReminderKeys) {
      if (reminderKey.startsWith(`${date}|`)) {
        sentReminderKeys.delete(reminderKey);
      }
    }
  }
}
