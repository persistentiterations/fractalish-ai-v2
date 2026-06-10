(function () {
  "use strict";

  var isLocal = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  var summaryEl = document.getElementById("summary");
  var scenariosEl = document.getElementById("scenarios");

  if (!isLocal) {
    summaryEl.innerHTML = "<p>Dashboard loads JSON only from localhost. Serve with: <code>python -m http.server 8001</code></p>";
    return;
  }

  fetch("../outputs/workbench_summary.json")
    .then(function (r) {
      if (!r.ok) throw new Error("Summary not found — run run_workbench.py first");
      return r.json();
    })
    .then(render)
    .catch(function (err) {
      summaryEl.innerHTML = "<p>" + err.message + "</p>";
    });

  function render(data) {
    var gc = data.guard_counts || {};
    summaryEl.innerHTML =
      "<div class=\"stats\">" +
      stat("PROCEED", gc.PROCEED || 0) +
      stat("HOLD", gc.HOLD || 0) +
      stat("WATCH", gc.WATCH || 0) +
      stat("REVERSE", gc.REVERSE || 0) +
      stat("Scars", data.contradiction_scars_created || 0) +
      stat("Overclaims blocked", data.overclaims_blocked || 0) +
      "</div>" +
      "<p>Final SessionGlyph hash: <code>" + (data.final_session_glyph_hash || "n/a") + "</code></p>" +
      "<p>SERA runtime total: <code>" + ((data.sera_summary && data.sera_summary.runtime_ms) || 0) + " ms</code></p>";

    var html = "";
    (data.scenario_results || []).forEach(function (s) {
      var cls = s.guard_decision === "HOLD" ? " scenario-card hold" : " scenario-card";
      html +=
        "<div class=\"" + cls.trim() + "\">" +
        "<strong>" + s.title + "</strong> " +
        "<span class=\"guard-badge " + s.guard_decision + "\">" + s.guard_decision + "</span> " +
        (s.assertions_passed ? "✓" : "✗") +
        "</div>";
    });
    scenariosEl.innerHTML = html || "<p>No scenarios in summary.</p>";
  }

  function stat(label, value) {
    return "<div class=\"stat\"><strong>" + value + "</strong>" + label + "</div>";
  }
})();