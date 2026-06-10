"""Demo: full activation spine — Natural Math, MCVA, runtime modules, SessionGlyph."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, export_decision_record, run_activation_event
from fractalish_ai.mcva.gate import evaluate_gate
from fractalish_ai.mcva.synthetic_examples import branching_trace
from fractalish_ai.natural_math.runner import run_comparison
from fractalish_ai.session_glyph import export_session_glyph

OUTPUT = ROOT / "outputs" / "demo_full_runtime"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    nm = run_comparison(OUTPUT / "natural_math")
    mcva = evaluate_gate(branching_trace()).to_dict()
    (OUTPUT / "mcva_record.json").write_text(json.dumps(mcva, indent=2), encoding="utf-8")

    basin = default_basin_state()
    basin["purpose"] = "full runtime v0.1 investor-safe demo"
    basin["operator_constraints"] = [
        "read_form_carefully",
        "preserve_uncertainty",
        "compare_before_claiming",
        "no_medical_or_disaster_claims",
    ]

    event = {
        "modality": "synthetic_evidence",
        "source": "fractalish_ai_v0.1_local",
        "content_summary": "Natural Math and MCVA gate completed; evaluate continuation.",
        "claim": "Morphology sample shows structured branching suitable for tentative comparison.",
        "evidence": [
            f"natural_math_efficiency_delta={nm['efficiency_delta']}",
            f"mcva_decision={mcva['decision']}",
            f"mcva_confidence={mcva['confidence']}",
        ],
        "confidence": mcva["confidence"],
        "risk_level": "low" if mcva["decision"] == "MCVA" else "medium",
        "speculation": mcva["decision"] == "HOLD",
        "similarity_claim": "branching morphology",
        "identity_claim": "",
        "purpose": basin["purpose"],
        "memory_delta": nm["efficiency_delta"],
        "provenance": {"natural_math": "local", "mcva": "synthetic_branching"},
        "domain_tags": ["synthetic", "morphology", "natural_math"],
    }

    record = run_activation_event(event, basin)
    export_decision_record(str(OUTPUT / "full_runtime_decision.json"), record)

    from fractalish_ai.session_glyph import SessionGlyph

    glyph_data = record["updated_session_glyph"]
    glyph = SessionGlyph(**{k: glyph_data[k] for k in SessionGlyph.__dataclass_fields__})
    export_session_glyph(str(OUTPUT / "session_glyph.json"), glyph)

    manifest = {
        "activation_id": record["updated_session_glyph"]["activation_id"],
        "guard_decision": record["guard_decision"]["decision"],
        "session_glyph_hash": record["updated_session_glyph"]["state_hash"],
        "natural_math_delta": nm["efficiency_delta"],
        "mcva_decision": mcva["decision"],
        "outputs": {
            "decision": str(OUTPUT / "full_runtime_decision.json"),
            "session_glyph": str(OUTPUT / "session_glyph.json"),
            "natural_math": str(OUTPUT / "natural_math" / "natural_math_comparison.json"),
            "mcva": str(OUTPUT / "mcva_record.json"),
        },
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print("Fractalish AI — Full Runtime Demo")
    print(f"Guard: {record['guard_decision']['decision']}")
    print(f"MCVA: {mcva['decision']}")
    print(f"Natural Math efficiency delta: {nm['efficiency_delta']}")
    print(f"SessionGlyph: {OUTPUT / 'session_glyph.json'}")
    print(f"Manifest: {OUTPUT / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())