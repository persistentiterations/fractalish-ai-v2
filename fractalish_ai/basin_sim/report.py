"""Simulation report writers for Cognitive Basin Simulation v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _scenario_md(result: dict[str, Any]) -> str:
    name = result.get("scenario_name", result.get("scenario", "unknown"))
    lines = [
        f"# Scenario: {name}",
        "",
        f"**Guard:** {result.get('guard_decision', '?')}",
        "",
    ]
    if result.get("narrative"):
        lines.append("## Narrative")
        for item in result["narrative"]:
            lines.append(f"- {item}")
    if result.get("assertions"):
        lines.extend(["", "## Assertions"])
        for k, v in result["assertions"].items():
            lines.append(f"- {k}: {'PASS' if v else 'FAIL'}")
    lines.extend([
        "",
        "## Layers",
        f"- PERCEPT: {bool(result.get('percept'))}",
        f"- ATAL threat/frustration: {result.get('atal', {}).get('threat')}/{result.get('atal', {}).get('frustration')}",
        f"- RIGOR findings: {len(result.get('rigor_findings', []))}",
        f"- Active attractors: {[a.get('node_id') for a in result.get('active_attractors', [])]}",
        f"- HOLD regions: {result.get('hold_regions', [])}",
    ])
    return "\n".join(lines)


def write_all_outputs(
    output_dir: Path,
    scenario_results: list[dict[str, Any]],
    summary: dict[str, Any],
    state: Any,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for result in scenario_results:
        name = result.get("scenario_name", result.get("scenario", "unknown"))
        (output_dir / f"scenario_{name}.json").write_text(
            json.dumps(result, indent=2, default=str), encoding="utf-8"
        )
        (output_dir / f"scenario_{name}.md").write_text(_scenario_md(result), encoding="utf-8")

    (output_dir / "cognitive_basin_sim_v1_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )

    md_lines = [
        "# Cognitive Basin Simulation v1 Summary",
        "",
        "Stateful basin simulation — not consciousness, not a chatbot.",
        "",
        summary.get("doctrine", ""),
        "",
        "## Guard counts",
    ]
    for k, v in summary.get("guard_counts", {}).items():
        md_lines.append(f"- {k}: {v}")
    md_lines.extend([
        "",
        f"**Contradiction scars:** {summary.get('contradiction_scars', 0)}",
        f"**Unresolved holds:** {summary.get('unresolved_holds', 0)}",
        f"**Recovery routes:** {summary.get('recovery_routes', 0)}",
        f"**HOLD/fog regions:** {summary.get('hold_fog_regions', [])}",
        "",
        f"**Final SessionGlyph hash:** `{summary.get('final_session_glyph_hash', '')}`",
        "",
        "## Scenarios",
    ])
    for item in summary.get("scenario_results", []):
        md_lines.append(f"- {item['name']}: {item['guard']}")
    (output_dir / "cognitive_basin_sim_v1_summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    fmm = summary.get("fractal_memory_map", {})
    (output_dir / "fractal_memory_map_snapshot.json").write_text(
        json.dumps(fmm, indent=2, default=str), encoding="utf-8"
    )
    glyph = summary.get("final_session_glyph", {})
    (output_dir / "final_session_glyph.json").write_text(
        json.dumps(glyph, indent=2, default=str), encoding="utf-8"
    )