import {
  hydrateRaidDates,
  removePastDates,
  saveRaidDates as saveRaidDatesCore,
  deleteRaidDates as deleteRaidDatesCore,
  displayRaidDates as displayRaidDatesCore,
  setDatesDisplayMax,
  hasRaidDate,
  getRaidDatesSnapshot,
} from './raid-dates.js';
import { loadDatesFromFile, writeDatesToFile } from './raid-storage.js';
import {
  setDatesReminderTime,
  getDatesReminderTime,
  setDatesReminderChannel,
  setDatesReminderMessage,
  formatDatesReminderMessage,
  getDatesReminderChannel,
  getDatesReminderMessage,
  getDueDateReminders as getDueDateRemindersCore,
} from './raid-reminder.js';

function cleanupPastDatesAndPersist() {
  const removedDates = removePastDates();

  if (removedDates.length > 0) {
    writeDatesToFile(getRaidDatesSnapshot());
  }
}

function initRaidHelper() {
  const storedDates = loadDatesFromFile();
  hydrateRaidDates(storedDates);
  cleanupPastDatesAndPersist();
}

export { setDatesDisplayMax, getRaidDatesSnapshot };
export {
  setDatesReminderTime,
  getDatesReminderTime,
  setDatesReminderChannel,
  setDatesReminderMessage,
  formatDatesReminderMessage,
  getDatesReminderChannel,
  getDatesReminderMessage,
};

export function saveRaidDates(datesInput) {
  cleanupPastDatesAndPersist();
  saveRaidDatesCore(datesInput);
  cleanupPastDatesAndPersist();
  writeDatesToFile(getRaidDatesSnapshot());
  return getRaidDatesSnapshot();
}

export function deleteRaidDates(datesInput) {
  cleanupPastDatesAndPersist();
  const { deletedDates } = deleteRaidDatesCore(datesInput);

  writeDatesToFile(getRaidDatesSnapshot());
  return getRaidDatesSnapshot();
}

export function displayRaidDates() {
  cleanupPastDatesAndPersist();
  return displayRaidDatesCore();
}

export function getDueDateReminders(now = new Date()) {
  cleanupPastDatesAndPersist();
  return getDueDateRemindersCore(hasRaidDate, now);
}

initRaidHelper();
