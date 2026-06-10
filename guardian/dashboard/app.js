async function loadSummary() {
  const res = await fetch("../outputs/dashboard_summary.json");
  if (!res.ok) throw new Error("Could not load dashboard_summary.json — run guardian/cli.py run-demo first");
  return res.json();
}

function renderStats(intakes) {
  const el = document.getElementById("stats");
  const holds = intakes.filter(i => i.decision === "HOLD" || i.decision === "REVERSE").length;
  const purged = intakes.filter(i => i.lifecycle_state === "PURGED").length;
  const flagged = intakes.filter(i => i.prompt_injection_flags.length > 0).length;

  el.innerHTML = [
    { label: "Total Intakes", value: intakes.length },
    { label: "HOLD / REVERSE", value: holds },
    { label: "Prompt Injection", value: flagged },
    { label: "Purged", value: purged },
  ].map(s => `
    <div class="stat-card">
      <div class="label">${s.label}</div>
      <div class="value">${s.value}</div>
    </div>
  `).join("");
}

function renderTable(intakes) {
  const el = document.getElementById("intake-table");
  if (!intakes.length) {
    el.innerHTML = "<p class='error'>No intake events found.</p>";
    return;
  }

  const rows = intakes.map(i => `
    <tr>
      <td>${i.file_name}</td>
      <td>${i.source_channel}</td>
      <td><span class="badge badge-${i.risk_level}">${i.risk_level}</span> ${i.risk_score}</td>
      <td>${i.decision}</td>
      <td>${i.lifecycle_state}</td>
      <td>${i.raw_model_visible ? "yes" : "no"} / ${i.sanitized_model_visible ? "yes" : "no"}</td>
      <td class="flags">${[...i.prompt_injection_flags, ...i.tool_poisoning_flags, ...i.hidden_instruction_flags].join(", ") || "—"}</td>
      <td class="derivatives">${Object.keys(i.derivative_artifacts || {}).length} artifacts</td>
    </tr>
  `).join("");

  el.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>File</th><th>Channel</th><th>Risk</th><th>Decision</th>
          <th>Lifecycle</th><th>Raw/San Vis</th><th>Flags</th><th>Derivatives</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>`;
}

function renderAudit(timeline) {
  const el = document.getElementById("audit-timeline");
  if (!timeline.length) {
    el.innerHTML = "<p>No audit entries yet.</p>";
    return;
  }
  el.innerHTML = timeline.slice(-20).reverse().map(a => `
    <div class="audit-entry">
      <strong>${a.action}</strong> — ${a.intake_id}
      <br>${a.before_state} → ${a.after_state} (${a.reason})
      <br><small>${a.timestamp} · ${a.actor}</small>
    </div>
  `).join("");
}

loadSummary()
  .then(data => {
    renderStats(data.intakes || []);
    renderTable(data.intakes || []);
    renderAudit(data.audit_timeline || []);
  })
  .catch(err => {
    document.body.insertAdjacentHTML("afterbegin",
      `<div class="error">${err.message}</div>`);
  });