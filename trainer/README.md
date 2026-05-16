# Apple Health Trainer

A personal trainer that reads your Apple Health data and recommends what to do today. Self-hosted Node service, Claude does the coaching.

```
iPhone ──(daily POST)──▶ /api/ingest ──▶ events.jsonl
                                              │
                                              ▼
                                      summarize last 14 days
                                              │
                                              ▼
   browser ──▶ /api/recommendation ──▶ Claude (claude-opus-4-7) ──▶ JSON rec
```

## Setup

```bash
cd trainer
npm install
cp .env.example .env
# edit .env: set ANTHROPIC_API_KEY and INGEST_TOKEN
npm start
```

Open <http://localhost:3000>.

## How data gets in

Read [`shortcut/README.md`](./shortcut/README.md). Either:

- **Health Auto Export** ($5 iOS app) — point its webhook at `/api/ingest`, done.
- **Apple Shortcuts** — build a Shortcut that reads HealthKit and POSTs JSON daily.

Either path sends a payload with your recent metrics and workouts; the trainer summarizes the last 14 days and asks Claude for a recommendation.

## API

| Endpoint                          | Method | What it does                                           |
| --------------------------------- | ------ | ------------------------------------------------------ |
| `/api/ingest`                     | POST   | Receive a health-data payload (auth: `X-Ingest-Token`) |
| `/api/summary?days=14`            | GET    | Aggregated view of recent metrics & workouts           |
| `/api/recommendation`             | GET    | Today's recommendation (cached up to 12h)              |
| `/api/recommendation?force=1`     | GET    | Bypass cache and regenerate                            |
| `/api/recommendation/refresh`     | POST   | Same, with optional `note` in body                     |
| `/api/health`                     | GET    | Quick sanity check                                     |

## What the recommendation looks like

```json
{
  "headline": "Easy zone-2 day — your HRV is recovering",
  "activity": "45-minute easy run or brisk walk, conversational pace",
  "intensity": "easy",
  "duration_minutes": 45,
  "rationale": "Sleep averaged 7.1h this week (good) but your HRV dropped 12% after Tuesday's hard session...",
  "watch_outs": ["Keep HR under 140", "Stop if RPE climbs above 4/10"],
  "alternative": "20-minute walk + mobility if you're not feeling it"
}
```

## Notes on the stack

- Node 20+, Express, no native deps (data is a JSONL log + a small JSON state file).
- Claude calls use **adaptive thinking** + `effort: "high"` and a JSON-schema constrained output, so the recommendation is always parseable.
- The system prompt is cached via `cache_control: { type: "ephemeral" }` — subsequent same-day refreshes are cheap.
- Recommendations are cached server-side for 12 hours unless you force a refresh.

## Deploying

This is intentionally lightweight — `npm start` behind a reverse proxy (Caddy, Nginx, Cloudflare Tunnel) is plenty. Make sure the public URL serves HTTPS so iOS will hit the webhook.
