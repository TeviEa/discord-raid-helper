const datesMemory = [];
let displayMaxDates = 10;

function normalizeInput(datesInput) {
  if (Array.isArray(datesInput)) {
    return datesInput;
  }

  if (typeof datesInput !== 'string') {
    throw new TypeError('datesInput must be a string or an array of strings');
  }

  return datesInput
    .split(/[\s,;]+/)
    .map((value) => value.trim())
    .filter(Boolean);
}

export function isValidRaidDate(dateString) {
  const match = /^(\d{2})\/(\d{2})\/(\d{2})$/.exec(dateString);
  if (!match) {
    return false;
  }

  const day = Number(match[1]);
  const month = Number(match[2]);
  const year = Number(match[3]);

  if (month < 1 || month > 12) {
    return false;
  }

  const fullYear = 2000 + year;
  const testDate = new Date(fullYear, month - 1, day);

  return (
    testDate.getFullYear() === fullYear &&
    testDate.getMonth() === month - 1 &&
    testDate.getDate() === day
  );
}

export function toSortableTimestamp(dateString) {
  const [day, month, year] = dateString.split('/').map(Number);
  return new Date(2000 + year, month - 1, day).getTime();
}

export function getTodayDateString(now = new Date()) {
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const year = String(now.getFullYear() % 100).padStart(2, '0');
  return `${day}/${month}/${year}`;
}

export function hydrateRaidDates(rawDates) {
  datesMemory.length = 0;

  if (!Array.isArray(rawDates)) {
    return;
  }

  for (const date of rawDates) {
    if (typeof date === 'string' && isValidRaidDate(date) && !datesMemory.includes(date)) {
      datesMemory.push(date);
    }
  }
}

export function getRaidDatesSnapshot() {
  return [...datesMemory];
}

export function hasRaidDate(date) {
  return datesMemory.includes(date);
}

export function removePastDates(now = new Date()) {
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const removedDates = [];

  for (let i = datesMemory.length - 1; i >= 0; i -= 1) {
    if (toSortableTimestamp(datesMemory[i]) < todayStart) {
      removedDates.push(datesMemory[i]);
      datesMemory.splice(i, 1);
    }
  }

  return removedDates;
}

export function setDatesDisplayMax(maxDates) {
  const parsedMax = Number(maxDates);

  if (!Number.isInteger(parsedMax) || parsedMax < 1) {
    throw new Error('Display max must be an integer greater than or equal to 1');
  }

  displayMaxDates = parsedMax;
  return displayMaxDates;
}

export function saveRaidDates(datesInput) {
  const dates = normalizeInput(datesInput);

  if (dates.length === 0) {
    throw new Error('No raid date provided');
  }

  const invalidDates = dates.filter((date) => !isValidRaidDate(date));
  if (invalidDates.length > 0) {
    throw new Error(`Invalid raid date format: ${invalidDates.join(', ')}`);
  }

  for (const date of dates) {
    if (!datesMemory.includes(date)) {
      datesMemory.push(date);
    }
  }

  return getRaidDatesSnapshot();
}

export function deleteRaidDates(datesInput) {
  const dates = normalizeInput(datesInput);

  if (dates.length === 0) {
    throw new Error('No raid date provided');
  }

  const deletedDates = [];

  for (const date of dates) {
    const index = datesMemory.indexOf(date);
    if (index !== -1) {
      deletedDates.push(date);
      datesMemory.splice(index, 1);
    }
  }

  return {
    dates: getRaidDatesSnapshot(),
    deletedDates,
  };
}

export function displayRaidDates() {
  if (datesMemory.length === 0) {
    return 'Aucune date de raid enregistree pour le moment.';
  }

  const sortedDates = [...datesMemory].sort(
    (a, b) => toSortableTimestamp(a) - toSortableTimestamp(b)
  );
  const displayedDates = sortedDates.slice(0, displayMaxDates);

  const lines = displayedDates.map((date) => `- ${date}`);
  return `Prochaines dates de raid:\n${lines.join('\n')}`;
}
