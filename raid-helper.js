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
  getDueDateReminders as getDueDateRemindersCore,
  markDateReminderSent,
  clearSentRemindersForDates,
} from './raid-reminder.js';

function cleanupPastDatesAndPersist() {
  const removedDates = removePastDates();

  if (removedDates.length > 0) {
    clearSentRemindersForDates(removedDates);
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
  markDateReminderSent,
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

  if (deletedDates.length > 0) {
    clearSentRemindersForDates(deletedDates);
  }

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
