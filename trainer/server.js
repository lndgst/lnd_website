import "dotenv/config";
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { appendEvent, readEvents, readState, writeState } from "./db.js";
import { generateRecommendation, summarizeEvents } from "./trainer-agent.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PORT = parseInt(process.env.PORT || "3000", 10);
const INGEST_TOKEN = process.env.INGEST_TOKEN;
const RECOMMENDATION_TTL_MS = 12 * 60 * 60 * 1000; // refresh recommendations at most twice a day

const app = express();
app.use(express.json({ limit: "20mb" }));
app.use(express.static(path.join(__dirname, "public")));

function timingSafeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string") return false;
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

function requireIngestToken(req, res, next) {
  if (!INGEST_TOKEN) {
    return res.status(500).json({ error: "INGEST_TOKEN is not configured on the server" });
  }
  const provided = req.header("x-ingest-token") || req.query.token;
  if (!timingSafeEqual(provided || "", INGEST_TOKEN)) {
    return res.status(401).json({ error: "invalid ingest token" });
  }
  next();
}

app.post("/api/ingest", requireIngestToken, (req, res) => {
  const body = req.body;
  if (!body || typeof body !== "object") {
    return res.status(400).json({ error: "expected JSON body" });
  }
  appendEvent({ source: req.header("x-ingest-source") || "unknown", payload: body });
  res.json({ ok: true });
});

app.get("/api/summary", async (req, res) => {
  const days = Math.max(1, Math.min(60, parseInt(req.query.days, 10) || 14));
  const events = await readEvents({ sinceDays: days });
  res.json({ events: events.length, summary: summarizeEvents(events) });
});

app.get("/api/recommendation", async (req, res) => {
  const state = readState();
  const cached = state.recommendation;
  const now = Date.now();
  const fresh = cached && now - new Date(cached.generatedAt).getTime() < RECOMMENDATION_TTL_MS;
  if (fresh && !req.query.force) {
    return res.json({ ...cached, cached: true });
  }

  try {
    const events = await readEvents({ sinceDays: 14 });
    const result = await generateRecommendation({ events, userNote: req.query.note });
    writeState({ ...state, recommendation: result });
    res.json({ ...result, cached: false });
  } catch (err) {
    console.error("recommendation failed:", err);
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/recommendation/refresh", async (req, res) => {
  try {
    const events = await readEvents({ sinceDays: 14 });
    const result = await generateRecommendation({
      events,
      userNote: req.body?.note,
    });
    const state = readState();
    writeState({ ...state, recommendation: result });
    res.json({ ...result, cached: false });
  } catch (err) {
    console.error("recommendation refresh failed:", err);
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/health", (req, res) => {
  res.json({
    ok: true,
    model: process.env.CLAUDE_MODEL || "claude-opus-4-7",
    has_api_key: !!process.env.ANTHROPIC_API_KEY,
    has_ingest_token: !!INGEST_TOKEN,
  });
});

app.listen(PORT, () => {
  console.log(`trainer running on http://localhost:${PORT}`);
  if (!process.env.ANTHROPIC_API_KEY) {
    console.warn("warning: ANTHROPIC_API_KEY is not set — recommendations will fail");
  }
  if (!INGEST_TOKEN) {
    console.warn("warning: INGEST_TOKEN is not set — /api/ingest will reject all requests");
  }
});
