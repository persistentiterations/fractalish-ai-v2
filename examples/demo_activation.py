"""Demo: start a bounded activation and record explicit state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, export_decision_record, run_activation_event

OUTPUT = ROOT / "outputs" / "demo_activation"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    basin = default_basin_state()
    basin["purpose"] = "bounded activation smoke test"
    basin["operator_constraints"] = ["no_medical_claims", "offline_only", "preserve_uncertainty"]

    event = {
        "modality": "text",
        "source": "operator@local",
        "content_summary": "Begin Fractalish AI v0.1 activation with traceable state.",
        "claim": "Activation can proceed with recorded constraints.",
        "evidence": ["local_runtime_ready"],
        "confidence": 0.75,
        "risk_level": "low",
        "purpose": basin["purpose"],
    }

    record = run_activation_event(event, basin)
    out_path = OUTPUT / "activation_decision.json"
    export_decision_record(str(out_path), record)

    print("Fractalish AI — Bounded Activation Demo")
    print(f"Guard: {record['guard_decision']['decision']}")
    print(f"Purpose: {basin['purpose']}")
    print(f"SessionGlyph hash: {record['updated_session_glyph']['state_hash']}")
    print(f"Output: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())