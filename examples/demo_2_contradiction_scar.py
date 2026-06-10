"""Demo 2: Contradiction Scar Test — conflicting sources preserved, routed to HOLD."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, export_decision_record, run_activation_event

OUTPUT = ROOT / "demo_outputs"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    basin = default_basin_state()
    basin["purpose"] = "reconcile conflicting source reports"
    basin["operator_constraints"] = ["preserve_both_sources", "no_forced_resolution"]

    event = {
        "modality": "text",
        "source": "source_b@local",
        "content_summary": "Source B reports metric M decreased; Source A reports M increased.",
        "claim": "Metric M direction is disputed between sources.",
        "evidence": [],
        "supported": False,
        "risk_level": "medium",
        "contradictions": [
            {"source": "source_a@local", "claim": "Metric M increased by 12%."},
            {"source": "source_b@local", "claim": "Metric M decreased by 8%."},
        ],
        "provenance": {
            "claim_a": "Metric M increased by 12%.",
            "claim_b": "Metric M decreased by 8%.",
            "source_a": "source_a@local",
            "source_b": "source_b@local",
        },
        "purpose": basin["purpose"],
    }

    record = run_activation_event(event, basin)
    out_path = OUTPUT / "demo_2_contradiction_scar.json"
    export_decision_record(str(out_path), record)

    guard = record["guard_decision"]["decision"]
    scars = record["updated_session_glyph"]["contradiction_scars"]
    contradiction = [f for f in record["rigor_findings"] if f["analyzer"] == "contradiction" and f["state"] == "HOLD"]
    sources_retained = {src for s in scars for src in (s["source_a"], s["source_b"])} if scars else set()

    print("Cognitive Basin Demo 2 — Contradiction Scar Test")
    print(f"Guard: {guard}")
    print(f"Contradiction detected: {bool(contradiction)}")
    print(f"Scars written: {len(scars)}")
    print(f"Sources retained: {sources_retained}")
    print(f"Output: {out_path}")

    ok = guard == "HOLD" and contradiction and scars and "source_a@local" in sources_retained
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())