import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

const mockFs = vi.hoisted(() => ({
  existsSync: vi.fn().mockReturnValue(false),
  readFileSync: vi.fn().mockReturnValue('{}'),
  writeFileSync: vi.fn(),
  mkdirSync: vi.fn(),
  renameSync: vi.fn(),
}));

vi.mock('node:fs', () => ({
  default: mockFs,
  ...mockFs,
}));

import {
  loadData,
  saveData,
  loadDatesFromFile,
  writeDatesToFile,
} from '../raid-storage.js';

describe('raid-storage', () => {
  let consoleError;

  beforeEach(() => {
    vi.clearAllMocks();
    mockFs.existsSync.mockReturnValue(false);
    mockFs.readFileSync.mockReturnValue('{}');
    // Suppress console.error from raid-storage.js error handling
    consoleError = console.error;
    console.error = vi.fn();
  });

  afterEach(() => {
    console.error = consoleError;
  });

  describe('loadData', () => {
    it('returns empty object when file does not exist', () => {
      const data = loadData();
      expect(data).toEqual({});
    });

    it('parses JSON from file', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(JSON.stringify({ dates: ['15/05/26'], reminder: { time: '18:00' } }));
      const data = loadData();
      expect(data).toEqual({ dates: ['15/05/26'], reminder: { time: '18:00' } });
    });

    it('returns empty object on parse error', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue('not json');
      const data = loadData();
      expect(data).toEqual({});
    });

    it('handles null JSON value', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue('null');
      const data = loadData();
      expect(data).toEqual({});
    });
  });

  describe('saveData', () => {
    it('writes JSON to temp file then renames', () => {
      saveData({ dates: ['15/05/26'] });
      expect(mockFs.writeFileSync).toHaveBeenCalled();
      expect(mockFs.renameSync).toHaveBeenCalled();
    });

    it('creates data directory if missing', () => {
      mockFs.existsSync.mockReturnValue(false);
      saveData({ dates: [] });
      expect(mockFs.mkdirSync).toHaveBeenCalledWith(expect.any(String), { recursive: true });
    });
  });

  describe('loadDatesFromFile', () => {
    it('returns dates array from file', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(JSON.stringify({ dates: ['15/05/26', '22/05/26'] }));
      const dates = loadDatesFromFile();
      expect(dates).toEqual(['15/05/26', '22/05/26']);
    });

    it('returns empty array when no dates in file', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(JSON.stringify({}));
      const dates = loadDatesFromFile();
      expect(dates).toEqual([]);
    });

    it('returns empty array when dates is not an array', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(JSON.stringify({ dates: 'not-an-array' }));
      const dates = loadDatesFromFile();
      expect(dates).toEqual([]);
    });
  });

  describe('writeDatesToFile', () => {
    it('writes dates to file', () => {
      mockFs.existsSync.mockReturnValue(true);
      mockFs.readFileSync.mockReturnValue(JSON.stringify({ dates: ['old'] }));
      writeDatesToFile(['15/05/26']);
      expect(mockFs.writeFileSync).toHaveBeenCalled();
      // Verify the written data contains the new dates
      const writeCall = mockFs.writeFileSync.mock.calls[0];
      const writtenData = JSON.parse(writeCall[1]);
      expect(writtenData.dates).toEqual(['15/05/26']);
    });
  });
});
