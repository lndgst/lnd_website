import Anthropic from "@anthropic-ai/sdk";

const MODEL = process.env.CLAUDE_MODEL || "claude-opus-4-7";

const SYSTEM_PROMPT = `You are a knowledgeable personal trainer and exercise physiologist. The user shares their recent Apple Health data with you and you recommend their next workout or rest day.

Your recommendations are grounded in:
- Recovery signals (sleep duration and quality, resting heart rate trends, HRV when available)
- Training load (recent workouts, active energy burned, step count)
- Variety and progression (avoid back-to-back high-intensity days, rotate muscle groups, build week over week)
- Safety (flag concerning patterns: sustained elevated resting HR, sharp HRV drop, sleep debt)

You produce a single concrete recommendation for today plus a short rationale. Keep it practical and motivating, not preachy. Use the user's actual numbers in your reasoning so they trust the recommendation.

Output strictly as JSON matching this schema:
{
  "headline": "short one-line title for today's recommendation (max 80 chars)",
  "activity": "specific activity, e.g. '45-minute easy zone 2 run' or 'full rest day'",
  "intensity": "rest" | "easy" | "moderate" | "hard",
  "duration_minutes": integer or null for rest,
  "rationale": "2-4 sentences referencing the user's recent data",
  "watch_outs": ["short bullet", "short bullet"],
  "alternative": "a lower-effort fallback if they're not feeling it"
}

Do not include any text outside the JSON object.`;

function summarizeEvents(events) {
  if (events.length === 0) {
    return { hasData: false, summary: "No data ingested yet." };
  }

  const metrics = {};
  const workouts = [];
  let latestTimestamp = null;

  for (const event of events) {
    const ts = event.received_at;
    if (!latestTimestamp || ts > latestTimestamp) latestTimestamp = ts;

    const payload = event.payload || event.data || event;

    if (Array.isArray(payload?.data?.metrics)) {
      for (const m of payload.data.metrics) {
        if (!m.name || !Array.isArray(m.data)) continue;
        metrics[m.name] ??= { units: m.units, points: [] };
        for (const point of m.data) {
          metrics[m.name].points.push(point);
        }
      }
    }
    if (Array.isArray(payload?.data?.workouts)) {
      workouts.push(...payload.data.workouts);
    }

    for (const key of [
      "step_count",
      "steps",
      "active_energy",
      "resting_heart_rate",
      "heart_rate_variability",
      "sleep_hours",
      "sleep",
    ]) {
      if (typeof payload?.[key] === "number") {
        metrics[key] ??= { units: null, points: [] };
        metrics[key].points.push({ date: ts, qty: payload[key] });
      }
    }
    if (payload?.workout && typeof payload.workout === "object") {
      workouts.push(payload.workout);
    }
  }

  const compact = {};
  for (const [name, { units, points }] of Object.entries(metrics)) {
    const sorted = points
      .filter((p) => p && (p.qty != null || p.value != null))
      .map((p) => ({ date: p.date, value: p.qty ?? p.value }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
    const recent = sorted.slice(-14);
    if (recent.length === 0) continue;
    const values = recent.map((p) => p.value).filter((v) => typeof v === "number");
    compact[name] = {
      units,
      count: recent.length,
      latest: recent[recent.length - 1],
      mean: values.length ? +(values.reduce((a, b) => a + b, 0) / values.length).toFixed(2) : null,
      min: values.length ? Math.min(...values) : null,
      max: values.length ? Math.max(...values) : null,
      series: recent,
    };
  }

  const recentWorkouts = workouts
    .map((w) => ({
      name: w.name || w.workoutActivityType || "workout",
      start: w.start || w.startDate || null,
      end: w.end || w.endDate || null,
      duration_seconds: w.duration ?? null,
      distance: w.distance ?? null,
      active_energy: w.active_energy ?? w.activeEnergyBurned ?? null,
    }))
    .filter((w) => w.start)
    .sort((a, b) => new Date(b.start) - new Date(a.start))
    .slice(0, 10);

  return {
    hasData: true,
    latestReceivedAt: latestTimestamp,
    metrics: compact,
    workouts: recentWorkouts,
  };
}

export async function generateRecommendation({ events, userNote }) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY is not set");
  }
  const client = new Anthropic({ apiKey });

  const summary = summarizeEvents(events);
  const today = new Date().toISOString().slice(0, 10);

  const userContent = [
    `Today is ${today}.`,
    "",
    "Recent Apple Health summary (last ~14 days):",
    "```json",
    JSON.stringify(summary, null, 2),
    "```",
    userNote ? `\nUser note: ${userNote}` : "",
    "",
    "Give me today's workout recommendation as JSON only.",
  ].join("\n");

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 4096,
    system: [
      {
        type: "text",
        text: SYSTEM_PROMPT,
        cache_control: { type: "ephemeral" },
      },
    ],
    thinking: { type: "adaptive" },
    output_config: {
      effort: "high",
      format: {
        type: "json_schema",
        schema: {
          type: "object",
          properties: {
            headline: { type: "string" },
            activity: { type: "string" },
            intensity: { type: "string", enum: ["rest", "easy", "moderate", "hard"] },
            duration_minutes: { type: ["integer", "null"] },
            rationale: { type: "string" },
            watch_outs: { type: "array", items: { type: "string" } },
            alternative: { type: "string" },
          },
          required: ["headline", "activity", "intensity", "rationale", "alternative"],
          additionalProperties: false,
        },
      },
    },
    messages: [{ role: "user", content: userContent }],
  });

  const textBlock = response.content.find((b) => b.type === "text");
  if (!textBlock) {
    throw new Error("No text block in response");
  }
  const recommendation = JSON.parse(textBlock.text);

  return {
    recommendation,
    summary,
    model: MODEL,
    generatedAt: new Date().toISOString(),
    usage: response.usage,
  };
}

export { summarizeEvents };
