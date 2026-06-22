import { describe, it, expect, beforeEach } from 'vitest';
import {
  isValidRaidDate,
  toSortableTimestamp,
  getTodayDateString,
  hydrateRaidDates,
  getRaidDatesSnapshot,
  hasRaidDate,
  saveRaidDates,
  deleteRaidDates,
  displayRaidDates,
  setDatesDisplayMax,
  removePastDates,
} from '../raid-dates.js';

describe('isValidRaidDate', () => {
  it('accepts valid dates', () => {
    expect(isValidRaidDate('01/01/26')).toBe(true);
    expect(isValidRaidDate('31/12/26')).toBe(true);
    expect(isValidRaidDate('15/05/26')).toBe(true);
    expect(isValidRaidDate('29/02/24')).toBe(true); // leap year
    expect(isValidRaidDate('28/02/23')).toBe(true); // non-leap year
  });

  it('rejects invalid day values', () => {
    expect(isValidRaidDate('32/05/26')).toBe(false);
    expect(isValidRaidDate('31/04/26')).toBe(false); // April has 30 days
    expect(isValidRaidDate('30/02/26')).toBe(false); // Feb never has 30 days
  });

  it('rejects invalid month values', () => {
    expect(isValidRaidDate('15/00/26')).toBe(false);
    expect(isValidRaidDate('15/13/26')).toBe(false);
  });

  it('rejects wrong format', () => {
    expect(isValidRaidDate('not-a-date')).toBe(false);
    expect(isValidRaidDate('15/5/26')).toBe(false); // single digit month
    expect(isValidRaidDate('15-05-26')).toBe(false);
    expect(isValidRaidDate('')).toBe(false);
    expect(isValidRaidDate('150526')).toBe(false);
  });
});

describe('toSortableTimestamp', () => {
  it('converts dates to sortable timestamps', () => {
    expect(toSortableTimestamp('01/01/26')).toBeLessThan(toSortableTimestamp('31/12/26'));
    expect(toSortableTimestamp('31/12/25')).toBeLessThan(toSortableTimestamp('01/01/26'));
    expect(toSortableTimestamp('15/05/26')).toBeGreaterThan(toSortableTimestamp('01/01/26'));
  });
});

describe('getTodayDateString', () => {
  it('returns date in DD/MM/YY format', () => {
    expect(getTodayDateString(new Date('2026-06-15T12:00:00Z'))).toBe('15/06/26');
  });

  it('pads single-digit day and month', () => {
    expect(getTodayDateString(new Date('2026-01-05T12:00:00Z'))).toBe('05/01/26');
  });

  it('handles year boundary', () => {
    expect(getTodayDateString(new Date('2026-12-31T12:00:00Z'))).toBe('31/12/26');
  });
});

describe('saveRaidDates', () => {
  beforeEach(() => {
    hydrateRaidDates([]);
  });

  it('adds valid comma-separated dates', () => {
    saveRaidDates('15/05/26,22/05/26');
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('deduplicates dates', () => {
    saveRaidDates('15/05/26,15/05/26');
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26']);
  });

  it('accepts array input', () => {
    saveRaidDates(['15/05/26', '22/05/26']);
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('accepts space-separated input', () => {
    saveRaidDates('15/05/26 22/05/26');
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('accepts semicolon-separated input', () => {
    saveRaidDates('15/05/26;22/05/26');
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('rejects empty string', () => {
    expect(() => saveRaidDates('')).toThrow('No raid date provided');
  });

  it('rejects invalid date format', () => {
    expect(() => saveRaidDates('invalid')).toThrow('Invalid raid date format');
  });

  it('rejects mix of valid and invalid dates', () => {
    expect(() => saveRaidDates('15/05/26,invalid')).toThrow('Invalid raid date format');
  });
});

describe('deleteRaidDates', () => {
  beforeEach(() => {
    hydrateRaidDates(['15/05/26', '22/05/26']);
  });

  it('deletes existing date', () => {
    const result = deleteRaidDates('15/05/26');
    expect(result.deletedDates).toEqual(['15/05/26']);
    expect(result.dates).toEqual(['22/05/26']);
  });

  it('ignores non-existing date', () => {
    const result = deleteRaidDates('01/01/26');
    expect(result.deletedDates).toEqual([]);
    expect(result.dates).toEqual(['15/05/26', '22/05/26']);
  });

  it('deletes multiple dates', () => {
    const result = deleteRaidDates('15/05/26,22/05/26');
    expect(result.deletedDates).toEqual(['15/05/26', '22/05/26']);
    expect(result.dates).toEqual([]);
  });

  it('rejects empty input', () => {
    expect(() => deleteRaidDates('')).toThrow('No raid date provided');
  });
});

describe('displayRaidDates', () => {
  beforeEach(() => {
    hydrateRaidDates([]);
    setDatesDisplayMax(10);
  });

  it('shows message when no dates', () => {
    expect(displayRaidDates()).toContain('Aucune date de raid');
  });

  it('shows sorted dates', () => {
    hydrateRaidDates(['15/05/26', '01/01/26', '31/12/26']);
    const result = displayRaidDates();
    const lines = result.split('\n').filter(l => l.startsWith('-'));
    expect(lines).toEqual(['- 01/01/26', '- 15/05/26', '- 31/12/26']);
  });

  it('respects display max', () => {
    setDatesDisplayMax(2);
    hydrateRaidDates(['01/01/26', '15/05/26', '31/12/26']);
    const result = displayRaidDates();
    const lines = result.split('\n').filter(l => l.startsWith('-'));
    expect(lines).toEqual(['- 01/01/26', '- 15/05/26']);
  });
});

describe('setDatesDisplayMax', () => {
  it('sets valid max', () => {
    expect(setDatesDisplayMax(5)).toBe(5);
  });

  it('rejects zero', () => {
    expect(() => setDatesDisplayMax(0)).toThrow('Display max must be an integer');
  });

  it('rejects negative', () => {
    expect(() => setDatesDisplayMax(-1)).toThrow('Display max must be an integer');
  });

  it('rejects non-integer', () => {
    expect(() => setDatesDisplayMax(1.5)).toThrow('Display max must be an integer');
  });

  it('rejects string', () => {
    expect(() => setDatesDisplayMax('abc')).toThrow('Display max must be an integer');
  });
});

describe('removePastDates', () => {
  it('removes dates before the given date', () => {
    const pastDate = new Date('2026-06-15T00:00:00Z');
    hydrateRaidDates(['01/06/26', '15/06/26', '01/07/26']);
    const removed = removePastDates(pastDate);
    expect(removed).toEqual(['01/06/26']);
    expect(getRaidDatesSnapshot()).toEqual(['15/06/26', '01/07/26']);
  });

  it('removes nothing when no past dates', () => {
    const futureDate = new Date('2026-06-01T00:00:00Z');
    hydrateRaidDates(['15/06/26', '01/07/26']);
    const removed = removePastDates(futureDate);
    expect(removed).toEqual([]);
    expect(getRaidDatesSnapshot()).toEqual(['15/06/26', '01/07/26']);
  });

  it('removes all dates when all are past', () => {
    const futureDate = new Date('2026-07-01T00:00:00Z');
    hydrateRaidDates(['01/06/26', '15/06/26']);
    const removed = removePastDates(futureDate);
    expect(removed).toEqual(['15/06/26', '01/06/26']);
    expect(getRaidDatesSnapshot()).toEqual([]);
  });
});

describe('hydrateRaidDates', () => {
  it('loads valid dates', () => {
    hydrateRaidDates(['15/05/26', '22/05/26']);
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('filters invalid dates', () => {
    hydrateRaidDates(['15/05/26', 'invalid', '22/05/26']);
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('deduplicates dates', () => {
    hydrateRaidDates(['15/05/26', '15/05/26', '22/05/26']);
    expect(getRaidDatesSnapshot()).toEqual(['15/05/26', '22/05/26']);
  });

  it('handles empty input', () => {
    hydrateRaidDates([]);
    expect(getRaidDatesSnapshot()).toEqual([]);
  });

  it('handles non-array input', () => {
    hydrateRaidDates('not-an-array');
    expect(getRaidDatesSnapshot()).toEqual([]);
  });
});

describe('hasRaidDate', () => {
  beforeEach(() => {
    hydrateRaidDates(['15/05/26', '22/05/26']);
  });

  it('returns true for existing dates', () => {
    expect(hasRaidDate('15/05/26')).toBe(true);
    expect(hasRaidDate('22/05/26')).toBe(true);
  });

  it('returns false for non-existing dates', () => {
    expect(hasRaidDate('01/01/26')).toBe(false);
  });
});
