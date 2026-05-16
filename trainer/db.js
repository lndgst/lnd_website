import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(__dirname, "data");
const EVENTS_PATH = path.join(DATA_DIR, "events.jsonl");
const STATE_PATH = path.join(DATA_DIR, "state.json");

fs.mkdirSync(DATA_DIR, { recursive: true });

export function appendEvent(event) {
  const line = JSON.stringify({ ...event, received_at: new Date().toISOString() }) + "\n";
  fs.appendFileSync(EVENTS_PATH, line);
}

export async function readEvents({ sinceDays = 14 } = {}) {
  if (!fs.existsSync(EVENTS_PATH)) return [];
  const cutoff = Date.now() - sinceDays * 24 * 60 * 60 * 1000;
  const events = [];
  const rl = readline.createInterface({
    input: fs.createReadStream(EVENTS_PATH),
    crlfDelay: Infinity,
  });
  for await (const line of rl) {
    if (!line.trim()) continue;
    try {
      const event = JSON.parse(line);
      const ts = new Date(event.received_at).getTime();
      if (ts >= cutoff) events.push(event);
    } catch {
      // skip malformed lines
    }
  }
  return events;
}

export function readState() {
  if (!fs.existsSync(STATE_PATH)) return {};
  try {
    return JSON.parse(fs.readFileSync(STATE_PATH, "utf8"));
  } catch {
    return {};
  }
}

export function writeState(state) {
  fs.writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
}
