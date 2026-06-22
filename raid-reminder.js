import { loadData, saveData } from './raid-storage.js';

let reminderHour = 18;
let reminderMinute = 0;
let reminderChannelId = null;
let reminderMessageTemplate = 'Rappel raid: la date {date} est aujourd\'hui.';


function loadReminderConfig() {
  const data = loadData();
  if (data && data.reminder) {
    const cfg = data.reminder;
    if (typeof cfg.time === 'string') {
      const m = /^(\d{2}):(\d{2})$/.exec(cfg.time.trim());
      if (m) {
        reminderHour = Number(m[1]);
        reminderMinute = Number(m[2]);
      }
    }
    if (typeof cfg.channelId === 'string') reminderChannelId = cfg.channelId;
    if (typeof cfg.message === 'string') reminderMessageTemplate = cfg.message;
  }
}

function saveReminderConfig() {
  const data = loadData();
  data.dates = Array.isArray(data.dates) ? data.dates : (data.dates ? data.dates : []);
  data.reminder = {
    time: `${String(reminderHour).padStart(2, '0')}:${String(reminderMinute).padStart(2, '0')}`,
    channelId: reminderChannelId,
    message: reminderMessageTemplate,
  };
  saveData(data);
}

// initialize from disk
loadReminderConfig();

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
  saveReminderConfig();
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
  saveReminderConfig();
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
  saveReminderConfig();
  return reminderMessageTemplate;
}

export function formatDatesReminderMessage(date) {
  return reminderMessageTemplate.replaceAll('{date}', date);
}

export function getDueDateReminders(hasDate, now = new Date()) {
  if (typeof hasDate !== 'function') {
    throw new TypeError('hasDate must be a function');
  }

  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();

  if (currentHour !== reminderHour || currentMinute !== reminderMinute) {
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
    dueReminders.push({ date: todayDateString, channelId });
  }

  return dueReminders;
}

export function getDatesReminderChannel() {
  return reminderChannelId;
}

export function getDatesReminderMessage() {
  return reminderMessageTemplate;
}
