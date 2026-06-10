"""Demo 1: False Continuity Test — prior unresolved claim must not be closed without evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, export_decision_record, run_activation_event

OUTPUT = ROOT / "demo_outputs"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    basin = default_basin_state()
    basin["purpose"] = "verify prior claim before continuation"
    basin["operator_constraints"] = ["no_false_closure", "hold_before_claiming"]

    # Step 1: establish prior unsupported claim → HOLD
    prior_event = {
        "modality": "text",
        "source": "operator@local",
        "content_summary": "Prior hypothesis: treatment X resolves condition Y.",
        "claim": "Treatment X resolves condition Y.",
        "evidence": [],
        "supported": False,
        "confidence": 0.4,
        "risk_level": "high",
        "purpose": basin["purpose"],
    }
    prior = run_activation_event(prior_event, basin)
    basin = prior["updated_basin_state"]

    # Step 2: attempt to continue as if settled
    continuation = {
        "modality": "text",
        "source": "operator@local",
        "content_summary": "Continue planning as if treatment X is confirmed effective.",
        "claim": "We can proceed because treatment X is confirmed effective.",
        "evidence": [],
        "supported": False,
        "assume_prior_settled": True,
        "confidence": 0.5,
        "risk_level": "high",
        "purpose": basin["purpose"],
    }
    record = run_activation_event(continuation, basin)
    out_path = OUTPUT / "demo_1_false_continuity.json"
    export_decision_record(str(out_path), record)

    guard = record["guard_decision"]["decision"]
    false_continuity = [f for f in record["rigor_findings"] if f["analyzer"] == "false_continuity"]
    missing = []
    for f in record["rigor_findings"]:
        missing.extend(f.get("evidence_missing", []))

    print("Cognitive Basin Demo 1 — False Continuity Test")
    print(f"Prior guard: {prior['guard_decision']['decision']}")
    print(f"Continuation guard: {guard}")
    print(f"False continuity detected: {bool(false_continuity)}")
    print(f"Missing evidence: {missing}")
    print(f"False closure prevented: {guard == 'HOLD'}")
    print(f"Output: {out_path}")

    return 0 if guard == "HOLD" and false_continuity else 1


if __name__ == "__main__":
    raise SystemExit(main())