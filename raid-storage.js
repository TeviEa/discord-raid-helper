import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR_PATH = path.join(__dirname, 'data');
const DATES_FILE_PATH = path.join(DATA_DIR_PATH, 'values.json');

function log(...args) {
  console.log(new Date().toISOString(), ...args);
}

function error(...args) {
  console.error(new Date().toISOString(), ...args);
}
export function loadData() {
  try {
    if (!fs.existsSync(DATES_FILE_PATH)) return {};
    const raw = fs.readFileSync(DATES_FILE_PATH, 'utf8');
    return JSON.parse(raw) || {};
  } catch (err) {
    error('Unable to read data file', DATES_FILE_PATH, err);
    return {};
  }
}

export function saveData(data) {
  try {
    if (!fs.existsSync(DATA_DIR_PATH)) fs.mkdirSync(DATA_DIR_PATH, { recursive: true });

    // atomic-ish write: write to temp file then rename
    const tmpPath = `${DATES_FILE_PATH}.tmp`;
    fs.writeFileSync(tmpPath, JSON.stringify(data, null, 2), 'utf8');
    fs.renameSync(tmpPath, DATES_FILE_PATH);
  } catch (err) {
    error('Unable to write data file', DATES_FILE_PATH, err);
  }
}

export function loadDatesFromFile() {
  const data = loadData();
  if (!Array.isArray(data.dates)) return [];
  return data.dates;
}

export function writeDatesToFile(dates) {
  const data = loadData();
  data.dates = dates;
  saveData(data);
}
