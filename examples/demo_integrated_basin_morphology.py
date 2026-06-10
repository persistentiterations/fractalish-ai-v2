"""Integrated demo: Natural Math process → MCVA morphology → Cognitive Basin guard."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.mcva.gate import evaluate_gate
from fractalish_ai.mcva.synthetic_examples import (
    branching_trace,
    irregular_boundary,
    noise_sample,
)
from fractalish_ai.natural_math.runner import run_comparison

OUTPUT = ROOT / "outputs"


def _scenario(name: str, sample: dict, claim: str, risk: str | None = None) -> dict:
    mcva = evaluate_gate(sample).to_dict()
    if risk is None:
        risk = "high" if mcva["decision"] in ("HOLD", "AMCVA") else "low"
    basin = default_basin_state()
    basin["purpose"] = f"integrated morphology interpretation: {name}"
    basin["operator_constraints"] = ["mcva_reads_cautiously", "hold_is_sacred", "no_overclaim"]

    event = {
        "modality": "process_trace_summary",
        "source": "natural_math_local",
        "content_summary": f"Process trace for {name}; MCVA={mcva['decision']}.",
        "claim": claim,
        "evidence": (
            [
                f"mcva_decision={mcva['decision']}",
                f"mcva_confidence={mcva['confidence']}",
                f"foreground_density={mcva['descriptors'].get('foreground_density')}",
            ]
            if mcva["decision"] == "MCVA"
            else []
        ),
        "supported": mcva["decision"] == "MCVA",
        "trace_metadata": {
            "mcva_decision": mcva["decision"],
            "mcva_confidence": mcva["confidence"],
        },
        "confidence": mcva["confidence"],
        "risk_level": risk,
        "speculation": mcva["decision"] in ("HOLD", "AMCVA"),
        "purpose": basin["purpose"],
        "provenance": {"morphology": name, "mcva": mcva["decision"]},
        "domain_tags": ["natural_math", "morphology", name],
    }

    if "proves intelligence" in claim.lower():
        event["supported"] = False
        event["risk_level"] = "high"

    record = run_activation_event(event, basin)
    return {
        "scenario": name,
        "mcva": mcva,
        "guard": record["guard_decision"]["decision"],
        "rigor_states": {f["analyzer"]: f["state"] for f in record["rigor_findings"]},
        "session_glyph_hash": record["updated_session_glyph"]["state_hash"],
        "sera": record["sera_record"],
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    nm_dir = OUTPUT / "integrated_natural_math"
    nm = run_comparison(nm_dir)

    results = [
        _scenario(
            "branching_trace",
            branching_trace(),
            "Branching morphology shows structured trace suitable for tentative comparison.",
        ),
        _scenario(
            "irregular_boundary",
            irregular_boundary(),
            "Irregular boundary morphology may indicate structured growth edge.",
        ),
        _scenario(
            "noise_non_diagnostic",
            noise_sample(),
            "Noise sample should not be used for positive morphology comparison.",
        ),
        _scenario(
            "overclaim_blocked",
            branching_trace(),
            "This branching trace proves intelligence and solves AI.",
            risk="high",
        ),
    ]

    summary = {
        "doctrine": {
            "natural_math": "process engine — generates bounded local growth",
            "fractalish_mcva": "morphology readout — MCVA / HOLD / AMCVA",
            "cognitive_basin": "state continuity — PERCEPT→ATAL→RIGOR→CIRCUIT→GUARD→SERA→SessionGlyph",
        },
        "natural_math_comparison": nm,
        "scenarios": results,
        "layer_bridge": (
            "Natural Math generates process. "
            "Fractalish reads the shape left by process. "
            "Cognitive Basin preserves reasoning state across process."
        ),
    }

    json_path = OUTPUT / "integrated_basin_morphology_summary.json"
    md_path = OUTPUT / "integrated_basin_morphology_summary.md"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    lines = [
        "# Integrated Basin / Morphology Summary",
        "",
        "Natural Math generates process. Fractalish reads the shape left by process. "
        "Cognitive Basin preserves reasoning state across process.",
        "",
        "## Natural Math (process)",
        f"- Efficiency delta: {nm.get('efficiency_delta')}",
        f"- Memory helped: {nm.get('success_delta', 0) > 0 or nm.get('revisit_delta', 0) > 0}",
        "",
        "## Scenarios",
    ]
    for r in results:
        lines.append(f"### {r['scenario']}")
        lines.append(f"- MCVA: {r['mcva']['decision']} (confidence={r['mcva']['confidence']})")
        lines.append(f"- GUARD: {r['guard']}")
        lines.append(f"- SessionGlyph hash: {r['session_glyph_hash']}")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("Integrated Basin / Morphology Demo")
    print(summary["layer_bridge"])
    print()
    for r in results:
        print(f"{r['scenario']}: MCVA={r['mcva']['decision']} → GUARD={r['guard']}")
    print()
    print(f"JSON: {json_path}")
    print(f"MD: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())