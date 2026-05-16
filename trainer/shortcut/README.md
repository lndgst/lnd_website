# Sending Apple Health data to the trainer

The trainer expects daily POSTs to `/api/ingest` with your recent Apple Health data. Two options.

## Option A — Health Auto Export (recommended)

[Health Auto Export](https://apps.apple.com/us/app/health-auto-export-json-csv/id1115567069) ($5 one-time) reads HealthKit on a schedule and POSTs JSON to a webhook. No Shortcut wiring required.

1. Install Health Auto Export on your iPhone.
2. **Settings → Automations → REST API → New Automation**.
   - URL: `https://<your-host>/api/ingest`
   - Method: `POST`
   - Headers: add `X-Ingest-Token` with the same value as `INGEST_TOKEN` in your `.env`.
3. Pick the metrics you care about. A useful default set:
   - Step Count
   - Active Energy
   - Resting Heart Rate
   - Heart Rate Variability
   - Sleep Analysis (hours)
   - Workouts (include workout details)
4. Schedule: daily, in the morning. The trainer keeps the last 14 days.

The payload arrives in the shape the trainer already understands:

```json
{
  "data": {
    "metrics": [{ "name": "step_count", "units": "count", "data": [{ "date": "...", "qty": 8234 }] }],
    "workouts": [{ "name": "Running", "start": "...", "duration": 1800 }]
  }
}
```

## Option B — iOS Shortcut

If you want to avoid the paid app, build a Shortcut that reads HealthKit and POSTs JSON.

1. Open **Shortcuts** on iPhone → **+** → New Shortcut.
2. Add these actions in order:
   - **Find Health Samples Where** → Type: Step Count, Date is in the last 7 days → save as variable `steps`.
   - Repeat for Resting Heart Rate, Sleep Analysis, Active Energy.
   - **Dictionary** action with this shape:
     ```
     {
       "step_count": <Average of steps>,
       "resting_heart_rate": <Average of resting hr>,
       "sleep_hours": <Average of sleep, divided by 3600>,
       "active_energy": <Sum of active energy>
     }
     ```
   - **Get Contents of URL**:
     - URL: `https://<your-host>/api/ingest`
     - Method: `POST`
     - Headers: `X-Ingest-Token: <your INGEST_TOKEN>`, `Content-Type: application/json`
     - Request Body: JSON → use the dictionary above.
3. Add a **Personal Automation** (Shortcuts → Automation → Time of Day) to run it every morning.

Option B sends a simpler shape. The trainer's summarizer accepts both.

## Testing without a phone

```bash
curl -X POST http://localhost:3000/api/ingest \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Token: $INGEST_TOKEN" \
  -d '{
    "step_count": 7400,
    "resting_heart_rate": 56,
    "sleep_hours": 7.3,
    "active_energy": 420,
    "workout": { "name": "Easy run", "start": "2026-05-15T08:00:00Z", "duration": 2400 }
  }'
```

Then visit `http://localhost:3000/` and hit refresh.
