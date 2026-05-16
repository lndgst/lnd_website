const recBody = document.getElementById("rec-body");
const summaryBody = document.getElementById("summary-body");
const dataStamp = document.getElementById("data-stamp");
const refreshBtn = document.getElementById("refresh-btn");

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderRecommendation(data) {
  if (data.error) {
    recBody.innerHTML = `<div class="error">${escapeHtml(data.error)}</div>`;
    return;
  }
  const r = data.recommendation;
  if (!r) {
    recBody.innerHTML = `<p class="muted">no recommendation yet</p>`;
    return;
  }
  const durationStr = r.duration_minutes ? ` · ${r.duration_minutes} min` : "";
  recBody.innerHTML = `
    <div class="headline">${escapeHtml(r.headline)}</div>
    <div class="activity-row">
      <span class="intensity ${escapeHtml(r.intensity)}">${escapeHtml(r.intensity)}</span>
      <span>${escapeHtml(r.activity)}${escapeHtml(durationStr)}</span>
    </div>
    <p class="rationale">${escapeHtml(r.rationale)}</p>
    ${
      Array.isArray(r.watch_outs) && r.watch_outs.length
        ? `<ul class="watch-outs">${r.watch_outs.map((w) => `<li>${escapeHtml(w)}</li>`).join("")}</ul>`
        : ""
    }
    ${r.alternative ? `<p class="alternative">${escapeHtml(r.alternative)}</p>` : ""}
    <p class="muted small" style="margin-top:12px">
      ${data.cached ? "cached" : "fresh"} · ${new Date(data.generatedAt).toLocaleString()}
    </p>
  `;
}

function formatMetricValue(name, value, units) {
  if (typeof value !== "number") return String(value ?? "—");
  if (name.includes("sleep")) return `${value.toFixed(1)} h`;
  if (name.includes("step")) return value.toFixed(0);
  if (name.includes("heart_rate") || name === "resting_heart_rate") return `${value.toFixed(0)} bpm`;
  if (name.includes("energy")) return `${value.toFixed(0)} kcal`;
  if (units) return `${value.toFixed(1)} ${units}`;
  return value.toFixed(1);
}

function renderSummary(data) {
  const summary = data.summary;
  if (!summary.hasData) {
    summaryBody.innerHTML = `<p class="muted">no data ingested yet — set up the shortcut to start sending your health data.</p>`;
    dataStamp.textContent = "";
    return;
  }
  dataStamp.textContent = `last received ${new Date(summary.latestReceivedAt).toLocaleString()}`;

  const metricCards = Object.entries(summary.metrics)
    .map(([name, m]) => {
      const latestVal = m.latest?.value;
      const avg = m.mean;
      return `
        <div class="metric">
          <div class="label">${escapeHtml(name.replaceAll("_", " "))}</div>
          <div class="value">${formatMetricValue(name, latestVal, m.units)}</div>
          <div class="meta">avg ${formatMetricValue(name, avg, m.units)} · n=${m.count}</div>
        </div>
      `;
    })
    .join("");

  const workouts = summary.workouts
    .slice(0, 5)
    .map((w) => {
      const date = w.start ? new Date(w.start).toLocaleDateString() : "—";
      const dur = w.duration_seconds ? `${Math.round(w.duration_seconds / 60)} min` : "";
      return `<li><span>${escapeHtml(w.name)} · ${escapeHtml(dur)}</span><span class="muted">${escapeHtml(date)}</span></li>`;
    })
    .join("");

  summaryBody.innerHTML = `
    ${metricCards ? `<div class="metric-grid">${metricCards}</div>` : `<p class="muted">no metrics yet</p>`}
    ${workouts ? `<h3 style="margin-top:20px;margin-bottom:8px;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;color:#888">recent workouts</h3><ul class="workouts">${workouts}</ul>` : ""}
  `;
}

async function loadRecommendation({ force = false } = {}) {
  refreshBtn.disabled = true;
  recBody.innerHTML = `<p class="muted">${force ? "asking your trainer…" : "loading…"}</p>`;
  try {
    const url = force ? "/api/recommendation?force=1" : "/api/recommendation";
    const res = await fetch(url);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    renderRecommendation(data);
  } catch (err) {
    recBody.innerHTML = `<div class="error">${escapeHtml(err.message)}</div>`;
  } finally {
    refreshBtn.disabled = false;
  }
}

async function loadSummary() {
  try {
    const res = await fetch("/api/summary");
    const data = await res.json();
    renderSummary(data);
  } catch (err) {
    summaryBody.innerHTML = `<div class="error">${escapeHtml(err.message)}</div>`;
  }
}

refreshBtn.addEventListener("click", () => loadRecommendation({ force: true }));

loadSummary();
loadRecommendation();
