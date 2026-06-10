"""Write per-scenario and aggregate workbench reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _scenario_md(result: dict[str, Any]) -> str:
    lines = [
        f"# {result['title']}",
        "",
        result["description"],
        "",
        f"**Guard decision:** {result['guard_decision']}",
        "",
        "## Narrative",
    ]
    for item in result.get("narrative", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Assertions"])
    for key, ok in result.get("assertions", {}).items():
        lines.append(f"- {key}: {'PASS' if ok else 'FAIL'}")
    if result.get("extras"):
        lines.extend(["", "## Extras", f"```json\n{json.dumps(result['extras'], indent=2)}\n```"])
    lines.extend([
        "",
        "## Layer snapshot",
        "- PERCEPT: structured intake recorded",
        "- ATAL: pressure fields updated (not truth)",
        "- RIGOR: integrity findings listed in JSON",
        "- CIRCUIT: memory routes / scars / holds updated",
        "- GUARD: ternary decision applied",
        "- SERA: cost and waste recorded",
        "- SessionGlyph: carry-forward state written",
    ])
    return "\n".join(lines)


def write_scenario_output(output_dir: Path, result: dict[str, Any]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    name = result["name"]
    json_path = output_dir / f"scenario_{name}.json"
    md_path = output_dir / f"scenario_{name}.md"
    json_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    md_path.write_text(_scenario_md(result), encoding="utf-8")
    return json_path, md_path


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    guard_counts = {"PROCEED": 0, "HOLD": 0, "WATCH": 0, "REVERSE": 0}
    scars_created = 0
    recovery_routes = 0
    unresolved_holds = 0
    overclaims_blocked = 0
    sera_totals = {
        "runtime_ms": 0.0,
        "hold_count": 0,
        "reverse_count": 0,
        "unsupported_claim_count": 0,
        "contradiction_count": 0,
    }

    for result in results:
        guard_counts[result["guard_decision"]] = guard_counts.get(result["guard_decision"], 0) + 1
        glyph = result.get("layers", {}).get("session_glyph", {})
        scars_created += len(glyph.get("contradiction_scars", []))
        recovery_routes += len(glyph.get("recovery_routes", []))
        unresolved_holds += len(glyph.get("unresolved_holds", []))
        if result["name"] == "overclaim_block":
            overclaims_blocked = len(result.get("extras", {}).get("blocked_claims", []))
        for record in result.get("records", []):
            sera = record.get("sera_record", {})
            sera_totals["runtime_ms"] += float(sera.get("runtime_ms", 0))
            sera_totals["hold_count"] += int(sera.get("hold_count", 0))
            sera_totals["reverse_count"] += int(sera.get("reverse_count", 0))
            sera_totals["unsupported_claim_count"] += int(sera.get("unsupported_claim_count", 0))
            sera_totals["contradiction_count"] += int(sera.get("contradiction_count", 0))

    final_glyph = results[-1].get("layers", {}).get("session_glyph", {}) if results else {}

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "doctrine": (
            "Natural Math generates process. "
            "Fractalish reads the shape left by process. "
            "Cognitive Basin preserves reasoning state across process."
        ),
        "framing": {
            "is": "traceable, stateful, ternary-gated cognition simulator",
            "is_not": "consciousness, sentience, chatbot, agent army, AGI proof",
        },
        "scenarios_run": [r["name"] for r in results],
        "scenario_results": [
            {
                "name": r["name"],
                "title": r["title"],
                "guard_decision": r["guard_decision"],
                "assertions_passed": all(r.get("assertions", {}).values()),
            }
            for r in results
        ],
        "guard_counts": guard_counts,
        "contradiction_scars_created": scars_created,
        "recovery_routes_created": recovery_routes,
        "unresolved_holds_carried_forward": unresolved_holds,
        "overclaims_blocked": overclaims_blocked,
        "sera_summary": {k: round(v, 2) if isinstance(v, float) else v for k, v in sera_totals.items()},
        "final_session_glyph_hash": final_glyph.get("state_hash", ""),
        "final_session_glyph": final_glyph,
    }


def write_summary(output_dir: Path, summary: dict[str, Any]) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "workbench_summary.json"
    md_path = output_dir / "workbench_summary.md"

    lines = [
        "# Cognitive Basin Workbench Summary",
        "",
        "Local, inspectable, stateful, ternary-gated behavioral simulation engine. **Not consciousness.**",
        "",
        summary["doctrine"],
        "",
        "## Guard decisions",
    ]
    for decision, count in summary["guard_counts"].items():
        lines.append(f"- {decision}: {count}")
    lines.extend([
        "",
        f"**Contradiction scars created:** {summary['contradiction_scars_created']}",
        f"**Recovery routes created:** {summary['recovery_routes_created']}",
        f"**Unresolved holds carried forward:** {summary['unresolved_holds_carried_forward']}",
        f"**Overclaims blocked:** {summary['overclaims_blocked']}",
        "",
        "## SERA summary",
        f"```json\n{json.dumps(summary['sera_summary'], indent=2)}\n```",
        "",
        f"**Final SessionGlyph hash:** `{summary['final_session_glyph_hash']}`",
        "",
        "## Scenarios",
    ])
    for item in summary["scenario_results"]:
        status = "PASS" if item["assertions_passed"] else "FAIL"
        lines.append(f"- {item['name']}: {item['guard_decision']} ({status})")

    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path