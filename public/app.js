async function loadJson(path) {
  try {
    const res = await fetch(path);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

function badge(decision) {
  const cls = (decision || "watch").toLowerCase();
  return `<span class="badge ${cls}">${decision || "—"}</span>`;
}

async function renderOutputs() {
  const el = document.getElementById("outputs");
  const manifest = await loadJson("../outputs/demo_full_runtime/manifest.json");
  const investor = await loadJson("../outputs/investor_demo_summary.json");
  const mcva = await loadJson("../outputs/demo_mcva/mcva_records.json");
  const nm = await loadJson("../outputs/demo_natural_math/natural_math_comparison.json");

  if (!manifest && !mcva && !nm) {
    el.innerHTML = "<p>Run <code>python examples/demo_full_runtime.py</code> first to generate outputs.</p>";
    return;
  }

  let html = "";

  if (manifest) {
    html += `<div class="panel"><h2>Last Activation</h2>
      <p>Guard: ${badge(manifest.guard_decision)} MCVA: ${badge(manifest.mcva_decision)}</p>
      <p>SessionGlyph hash: <code>${manifest.session_glyph_hash || "—"}</code></p>
      <p>Natural Math efficiency delta: <code>${manifest.natural_math_delta ?? "—"}</code></p></div>`;
  }

  if (mcva) {
    html += `<div class="panel"><h2>MCVA Gate Results</h2><ul class="compact">`;
    mcva.forEach((r) => {
      html += `<li>${r.descriptors?.sample_name || "sample"}: ${badge(r.decision)} (${r.confidence})</li>`;
    });
    html += `</ul></div>`;
  }

  if (nm) {
    const b = nm.baseline;
    const m = nm.memory_enabled;
    html += `<div class="panel"><h2>Natural Math Comparison</h2>
      <ul class="compact">
        <li>Baseline: success=${b.success}, steps=${b.total_steps}, revisits=${b.revisits}</li>
        <li>Memory: success=${m.success}, steps=${m.total_steps}, revisits=${m.revisits}</li>
        <li>Efficiency delta: <code>${nm.efficiency_delta}</code></li>
      </ul></div>`;
  }

  if (investor) {
    html += `<div class="panel"><h2>Investor Packet</h2>
      <p>Generated: <code>${investor.generated_at || "—"}</code></p>
      <p>SessionGlyph: <code>${investor.session_glyph_hash || "—"}</code></p>
      <p>See <code>outputs/investor_demo_summary.md</code></p></div>`;
  }

  el.innerHTML = html;
}

document.addEventListener("DOMContentLoaded", renderOutputs);