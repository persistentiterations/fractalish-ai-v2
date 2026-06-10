(function () {
  "use strict";
  var local = location.hostname === "localhost" || location.hostname === "127.0.0.1";
  if (!local) return;

  Promise.all([
    fetch("../outputs/cognitive_basin_sim_v1_summary.json").then(function (r) { return r.json(); }),
    fetch("../outputs/fractal_memory_map_snapshot.json").then(function (r) { return r.json(); })
  ]).then(function (data) {
    var summary = data[0];
    var fmm = data[1];
    var gc = summary.guard_counts || {};
    document.getElementById("summary").innerHTML =
      "<div class=\"stats\">" +
      stat("PROCEED", gc.PROCEED) + stat("HOLD", gc.HOLD) +
      stat("WATCH", gc.WATCH) + stat("REVERSE", gc.REVERSE) +
      "</div>" +
      "<p>SessionGlyph hash: <code>" + (summary.final_session_glyph_hash || "n/a") + "</code></p>" +
      "<p>HOLD/fog: " + (summary.hold_fog_regions || []).length + " | Scars: " + (summary.contradiction_scars || 0) + "</p>";

    var sh = "";
    (summary.scenario_results || []).forEach(function (s) {
      sh += "<div class=\"scenario-row\"><span class=\"badge " + s.guard + "\">" + s.guard + "</span> " + s.name + "</div>";
    });
    document.getElementById("scenarios").innerHTML = sh || "<p>No scenarios.</p>";

    var fh = "<p>Nodes: " + Object.keys(fmm.nodes || {}).length + " | Links: " + (fmm.links || []).length + "</p>";
    (summary.active_attractors || []).slice(0, 5).forEach(function (a) {
      fh += "<div class=\"fmm-node\">★ " + a.node_id + " (score " + a.attractor_score + ")</div>";
    });
    document.getElementById("fmm").innerHTML = fh;
  }).catch(function (e) {
    document.getElementById("summary").innerHTML = "<p>" + e.message + "</p>";
  });

  function stat(label, val) {
    return "<div class=\"stat\"><strong>" + (val || 0) + "</strong>" + label + "</div>";
  }
})();