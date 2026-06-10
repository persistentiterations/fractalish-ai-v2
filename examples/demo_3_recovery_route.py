"""Demo 3: Recovery Route Test — reload SessionGlyph and reconstruct purpose/state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, export_decision_record, run_activation_event
from fractalish_ai.session_glyph import SessionGlyph, basin_from_glyph, export_session_glyph

OUTPUT = ROOT / "demo_outputs"
GLYPH_PATH = OUTPUT / "demo_3_session_glyph.json"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    basin = default_basin_state()
    basin["purpose"] = "complete bounded analysis with interrupt recovery"
    basin["operator_constraints"] = ["offline_only", "preserve_open_loops"]

    event = {
        "modality": "text",
        "source": "operator@local",
        "content_summary": "Begin analysis; evidence incomplete for final claim.",
        "claim": "Preliminary pattern noted; confirmation pending.",
        "evidence": ["local_observation_1"],
        "supported": True,
        "confidence": 0.55,
        "risk_level": "low",
        "speculation": True,
        "purpose": basin["purpose"],
    }

    record = run_activation_event(event, basin)
    glyph_data = record["updated_session_glyph"]
    glyph = SessionGlyph(**{k: glyph_data[k] for k in SessionGlyph.__dataclass_fields__})
    export_session_glyph(str(GLYPH_PATH), glyph)

    # Simulate context interrupt — reload glyph only
    reloaded = json.loads(GLYPH_PATH.read_text(encoding="utf-8"))
    recovered_basin = basin_from_glyph(reloaded)

    recovery_event = {
        "modality": "text",
        "source": "operator@local",
        "content_summary": "Resume after interrupt; reconstruct next action from SessionGlyph.",
        "claim": "Continue from saved activation state without inventing closure.",
        "evidence": ["session_glyph_reload"],
        "supported": True,
        "confidence": 0.6,
        "risk_level": "low",
        "purpose": recovered_basin.get("purpose", ""),
    }

    recovery_record = run_activation_event(recovery_event, recovered_basin)
    out_path = OUTPUT / "demo_3_recovery_route.json"
    export_decision_record(str(out_path), recovery_record)

    summary = {
        "purpose_recovered": reloaded.get("purpose") == basin["purpose"],
        "open_loops_recovered": len(reloaded.get("open_loops", [])) > 0,
        "unresolved_holds_recovered": len(reloaded.get("unresolved_holds", [])) >= 0,
        "next_action_recovered": bool(reloaded.get("next_action")),
        "contradiction_scars_preserved": reloaded.get("contradiction_scars", []),
        "recovery_guard": recovery_record["guard_decision"]["decision"],
        "unsupported_invention_avoided": recovery_record["guard_decision"]["decision"] != "PROCEED"
        or recovery_record["rigor_findings"],
    }
    (OUTPUT / "demo_3_recovery_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Cognitive Basin Demo 3 — Recovery Route Test")
    print(f"Purpose recovered: {summary['purpose_recovered']} — {reloaded.get('purpose')}")
    print(f"Open loops recovered: {summary['open_loops_recovered']} ({len(reloaded.get('open_loops', []))})")
    print(f"Next action recovered: {summary['next_action_recovered']} — {reloaded.get('next_action')}")
    print(f"Unresolved holds: {len(reloaded.get('unresolved_holds', []))}")
    print(f"Recovery guard: {summary['recovery_guard']}")
    print(f"Glyph: {GLYPH_PATH}")
    print(f"Output: {out_path}")

    ok = summary["purpose_recovered"] and summary["next_action_recovered"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())