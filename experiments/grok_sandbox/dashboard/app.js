async function loadJson(path) {
  try {
    const r = await fetch(path);
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}

function renderTable(rows) {
  if (!rows || !rows.length) return "<p>No benchmark data. Run run_maze_benchmark.py first.</p>";
  const cols = ["maze_name", "mode", "success_rate", "mean_steps", "mean_revisits", "mean_efficiency_score"];
  let html = "<table><tr>" + cols.map((c) => `<th>${c}</th>`).join("") + "</tr>";
  for (const row of rows) {
    html += "<tr>" + cols.map((c) => `<td>${row[c] ?? ""}</td>`).join("") + "</tr>";
  }
  return html + "</table>";
}

async function init() {
  // Local-only: fetch works when served via python -m http.server (no CDN).
  const data = await loadJson("../outputs/maze_benchmark_summary.json");
  const el = document.getElementById("results");
  const best = document.getElementById("best-modes");
  const interp = document.getElementById("interpretation");

  if (!data) {
    el.innerHTML = "<p>Run: <code>python experiments/grok_sandbox/benchmark/run_maze_benchmark.py</code></p>";
    return;
  }

  el.innerHTML = renderTable(data.aggregate_by_maze_mode);
  if (data.best_mode_per_maze) {
    best.innerHTML = "<ul>" + Object.entries(data.best_mode_per_maze)
      .map(([m, mode]) => `<li><strong>${m}</strong>: <code>${mode}</code></li>`).join("") + "</ul>";
  }
  if (data.interpretation) {
    interp.innerHTML = "<ul>" + Object.values(data.interpretation)
      .map((t) => `<li>${t}</li>`).join("") + "</ul>";
  }
}

document.addEventListener("DOMContentLoaded", init);