"""Demo: spec-first FractalMemoryMap + ReceptorEvent + BasinLink contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.basin_link import BasinLink, receptor_event_to_decision_record
from fractalish_ai.fractal_memory_map import FractalMemoryLink, FractalMemoryMap, FractalMemoryNode
from fractalish_ai.receptors import ReceptorType, create_receptor_event, to_percept_event

OUTPUT = ROOT / "outputs" / "demo_spec_first_contracts"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)

    receptor = create_receptor_event(
        receptor_type=ReceptorType.HUMAN_NOTE,
        source="operator@fieldnode",
        raw_summary="Operator note: compare maze memory trace with prior morphology hold.",
        possible_claims=["Memory-enabled run may have fewer revisits in controlled benchmark."],
        missing_context=["full_benchmark_run_id"],
        domain_tags=["contract_demo", "human_note"],
    )
    percept_event = to_percept_event(receptor)

    fmm = FractalMemoryMap(center_node_id="hub")
    fmm.add_node(
        FractalMemoryNode(
            node_id="hub",
            label="activation hub",
            salience=0.8,
            replay_score=0.5,
            current_distance_from_center=0.0,
            source="basin@local",
        )
    )
    fmm.add_node(
        FractalMemoryNode(
            node_id="maze_mem",
            label="maze memory trace",
            salience=0.7,
            replay_score=0.6,
            current_distance_from_center=0.4,
            source="grok_sandbox",
            domain_tags=["maze", "benchmark"],
        )
    )
    fmm.add_node(
        FractalMemoryNode(
            node_id="morph_hold",
            label="irregular boundary hold",
            salience=0.9,
            replay_score=0.8,
            current_distance_from_center=0.3,
            source="mcva@local",
            domain_tags=["morphology", "hold"],
        )
    )
    fmm.add_node(
        FractalMemoryNode(
            node_id="conflict_a",
            label="source A metric up",
            salience=0.5,
            source="a@local",
        )
    )
    fmm.add_node(
        FractalMemoryNode(
            node_id="conflict_b",
            label="source B metric down",
            salience=0.5,
            source="b@local",
        )
    )

    fmm.add_link(
        FractalMemoryLink(
            source_node="hub",
            target_node="maze_mem",
            relation_type="analogy",
            strength=0.6,
            replay_validated=True,
            notes="analogy link — not identity",
        )
    )
    fmm.add_contradiction_link("conflict_a", "conflict_b", notes="both preserved")
    fmm.mark_hold_region("morph_hold")

    attractors = fmm.nearest_active_attractors()
    attractor_ids = [a["node_id"] for a in attractors]

    link = BasinLink(
        activation_id="contract-demo-activation",
        purpose="spec-first contract demonstration",
        operator_constraints=["local_only", "hold_is_sacred", "no_false_closure"],
        fractal_memory_map=fmm.to_dict(),
    )
    record = receptor_event_to_decision_record(receptor, link)

    summary = {
        "receptor_type": receptor.receptor_type,
        "percept_supported": percept_event["supported"],
        "percept_intake_layer": percept_event["provenance"]["intake_layer"],
        "fractal_memory_map_nodes": len(fmm.nodes),
        "contradiction_links": sum(1 for l in fmm.links if l.relation_type == "contradiction"),
        "hold_regions": sorted(fmm.hold_regions),
        "attractor_ids": attractor_ids,
        "morph_hold_excluded": "morph_hold" not in attractor_ids,
        "guard_decision": record["guard_decision"]["decision"],
        "activation_id_preserved": record["updated_session_glyph"]["activation_id"],
        "session_glyph_hash": record["updated_session_glyph"]["state_hash"],
    }

    (OUTPUT / "contract_demo_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTPUT / "fractal_memory_map.json").write_text(
        json.dumps(fmm.to_dict(), indent=2), encoding="utf-8"
    )

    print("Spec-First Basin Contracts Demo")
    print(f"ReceptorEvent: {receptor.receptor_type} → PERCEPT (supported={percept_event['supported']})")
    print(f"FractalMemoryMap nodes: {len(fmm.nodes)}")
    print(f"Contradiction links: {summary['contradiction_links']}")
    print(f"HOLD region: morph_hold — excluded from attractors: {summary['morph_hold_excluded']}")
    print(f"Clean attractors: {attractor_ids}")
    print(f"BasinLink GUARD: {summary['guard_decision']}")
    print(f"Activation ID preserved: {summary['activation_id_preserved']}")
    print(f"Output: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())