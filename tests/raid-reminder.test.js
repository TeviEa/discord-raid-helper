import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock at top level (hoisted)
const mockLoadData = vi.fn().mockReturnValue({ dates: [], reminder: {} });
const mockSaveData = vi.fn();

vi.mock('../raid-storage.js', () => ({
  loadData: mockLoadData,
  saveData: mockSaveData,
}));

describe('raid-reminder', () => {
  let reminderModule;

  beforeEach(async () => {
    vi.resetModules();
    mockLoadData.mockReturnValue({ dates: [], reminder: {} });
    mockSaveData.mockClear();
    reminderModule = await import('../raid-reminder.js');
  });

  describe('setDatesReminderTime', () => {
    it('sets valid time', () => {
      expect(reminderModule.setDatesReminderTime('18:30')).toBe('18:30');
      expect(mockSaveData).toHaveBeenCalled();
    });

    it('sets midnight', () => {
      expect(reminderModule.setDatesReminderTime('00:00')).toBe('00:00');
    });

    it('sets end of day', () => {
      expect(reminderModule.setDatesReminderTime('23:59')).toBe('23:59');
    });

    it('rejects invalid time format', () => {
      expect(() => reminderModule.setDatesReminderTime('abc')).toThrow('HH:mm format');
    });

    it('rejects invalid hour (too high)', () => {
      expect(() => reminderModule.setDatesReminderTime('25:00')).toThrow('valid 24h time');
    });

    it('rejects invalid minute (too high)', () => {
      expect(() => reminderModule.setDatesReminderTime('18:60')).toThrow('valid 24h time');
    });

    it('rejects non-string input', () => {
      expect(() => reminderModule.setDatesReminderTime(123)).toThrow('must be a string');
    });
  });

  describe('getDatesReminderTime', () => {
    it('returns the configured time', () => {
      reminderModule.setDatesReminderTime('14:30');
      expect(reminderModule.getDatesReminderTime()).toBe('14:30');
    });
  });

  describe('setDatesReminderChannel', () => {
    it('sets valid channel id', () => {
      const result = reminderModule.setDatesReminderChannel('123456789');
      expect(result).toBe('123456789');
      expect(mockSaveData).toHaveBeenCalled();
    });

    it('rejects non-string input', () => {
      expect(() => reminderModule.setDatesReminderChannel(123)).toThrow('must be a valid Discord channel id');
    });

    it('rejects channel with non-digit characters', () => {
      expect(() => reminderModule.setDatesReminderChannel('abc')).toThrow('must be a valid Discord channel id');
      expect(() => reminderModule.setDatesReminderChannel('123abc')).toThrow('must be a valid Discord channel id');
    });
  });

  describe('setDatesReminderMessage', () => {
    it('sets valid message', () => {
      const msg = "Rappel raid aujourd'hui ({date})";
      expect(reminderModule.setDatesReminderMessage(msg)).toBe(msg);
      expect(mockSaveData).toHaveBeenCalled();
    });

    it('trims whitespace', () => {
      const result = reminderModule.setDatesReminderMessage('  test  ');
      expect(result).toBe('test');
    });

    it('rejects empty string', () => {
      expect(() => reminderModule.setDatesReminderMessage('')).toThrow('cannot be empty');
    });

    it('rejects whitespace-only string', () => {
      expect(() => reminderModule.setDatesReminderMessage('   ')).toThrow('cannot be empty');
    });

    it('rejects too long message (> 2000 chars)', () => {
      expect(() => reminderModule.setDatesReminderMessage('x'.repeat(2001))).toThrow('cannot exceed 2000 characters');
    });

    it('rejects non-string input', () => {
      expect(() => reminderModule.setDatesReminderMessage(123)).toThrow('must be a string');
    });
  });

  describe('formatDatesReminderMessage', () => {
    it('replaces {date} placeholder', () => {
      reminderModule.setDatesReminderMessage('Rappel: {date}');
      const result = reminderModule.formatDatesReminderMessage('15/05/26');
      expect(result).toBe('Rappel: 15/05/26');
    });
  });

  describe('getDatesReminderChannel', () => {
    it('returns the configured channel', () => {
      reminderModule.setDatesReminderChannel('123456');
      expect(reminderModule.getDatesReminderChannel()).toBe('123456');
    });
  });

  describe('getDatesReminderMessage', () => {
    it('returns the configured message', () => {
      reminderModule.setDatesReminderMessage('test message');
      expect(reminderModule.getDatesReminderMessage()).toBe('test message');
    });
  });

  describe('getDueDateReminders', () => {
    // Helper: create a local-date Date object (hours/minutes are in local TZ)
    const localDate = (year, month, day, hour, minute = 0) =>
      new Date(year, month, day, hour, minute);

    it('returns empty array when time does not match', () => {
      const mockHasDate = vi.fn().mockReturnValue(true);
      const now = localDate(2026, 5, 15, 14, 0); // 14:00 local, default reminder is 18:00
      const result = reminderModule.getDueDateReminders(mockHasDate, now);
      expect(result).toEqual([]);
    });

    it('returns empty array when no date for today', () => {
      reminderModule.setDatesReminderTime('14:00');
      const mockHasDate = vi.fn().mockReturnValue(false);
      const now = localDate(2026, 5, 15, 14, 0);
      const result = reminderModule.getDueDateReminders(mockHasDate, now);
      expect(result).toEqual([]);
    });

    it('returns reminder when time matches and date exists', () => {
      reminderModule.setDatesReminderTime('10:00');
      reminderModule.setDatesReminderChannel('123456');
      const mockHasDate = vi.fn().mockReturnValue(true);
      const now = localDate(2026, 5, 15, 10, 0);
      const result = reminderModule.getDueDateReminders(mockHasDate, now);
      expect(result).toHaveLength(1);
      expect(result[0]).toHaveProperty('channelId', '123456');
      expect(result[0]).toHaveProperty('date');
    });

    it('returns empty when no channel configured', () => {
      reminderModule.setDatesReminderTime('10:00');
      // Channel is null by default (from empty reminder config)
      const mockHasDate = vi.fn().mockReturnValue(true);
      const now = localDate(2026, 5, 15, 10, 0);
      const result = reminderModule.getDueDateReminders(mockHasDate, now);
      expect(result).toEqual([]);
    });
  });
});
