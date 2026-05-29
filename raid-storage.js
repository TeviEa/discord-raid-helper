import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DATA_DIR_PATH = path.join(__dirname, 'data');
const DATES_FILE_PATH = path.join(DATA_DIR_PATH, 'raid-dates.json');

export function loadDatesFromFile() {
  try {
    if (!fs.existsSync(DATES_FILE_PATH)) {
      return [];
    }

    const raw = fs.readFileSync(DATES_FILE_PATH, 'utf8');
    const parsed = JSON.parse(raw);

    if (!Array.isArray(parsed.dates)) {
      return [];
    }

    return parsed.dates;
  } catch (error) {
    console.error('Unable to read raid dates file', error);
    return [];
  }
}

export function writeDatesToFile(dates) {
  try {
    if (!fs.existsSync(DATA_DIR_PATH)) {
      fs.mkdirSync(DATA_DIR_PATH, { recursive: true });
    }

    fs.writeFileSync(
      DATES_FILE_PATH,
      JSON.stringify({ dates }, null, 2),
      'utf8'
    );
  } catch (error) {
    console.error('Unable to write raid dates file', error);
  }
}
