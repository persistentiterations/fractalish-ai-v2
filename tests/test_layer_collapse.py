"""Mandatory layer-collapse prevention tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.atal import AtalState
from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.fractal_memory_map import FractalMemoryMap, FractalMemoryNode
from fractalish_ai.guard import evaluate_guard
from fractalish_ai.mcva.gate import evaluate_gate
from fractalish_ai.mcva.synthetic_examples import branching_trace, irregular_boundary
from fractalish_ai.receptors import create_receptor_event, to_percept_event
from fractalish_ai.rigor import run_rigor_checks


def test_mcva_cannot_short_circuit_guard() -> None:
    """MCVA=MCVA on morphology does not force GUARD=PROCEED without RIGOR."""
    mcva = evaluate_gate(branching_trace())
    assert mcva.decision == "MCVA"

    event = {
        "modality": "morphology",
        "source": "mcva@local",
        "claim": "This branching trace proves consciousness.",
        "content_summary": "Overclaim on MCVA-positive morphology.",
        "evidence": [],
        "supported": False,
        "risk_level": "high",
        "provenance": {"mcva_decision": mcva.decision},
    }
    findings = [f.to_dict() for f in run_rigor_checks(event)]
    guard = evaluate_guard(findings, event)
    assert guard.decision == "HOLD"

    record = run_activation_event(event, default_basin_state())
    assert record["guard_decision"]["decision"] == "HOLD"
    assert mcva.decision == "MCVA"


def test_atal_pressure_cannot_set_claim_supported() -> None:
    """High ATAL pressure fields do not make unsupported claim supported."""
    basin = default_basin_state()
    basin["atal"] = AtalState(
        frustration=0.95,
        threat=0.9,
        uncertainty=0.92,
        coherence=0.1,
    ).to_dict()

    event = {
        "modality": "text",
        "source": "urgent@local",
        "claim": "Critical action required immediately.",
        "content_summary": "High pressure, no evidence.",
        "evidence": [],
        "supported": False,
        "risk_level": "high",
        "uncertainty": 0.9,
        "confidence": 0.2,
    }
    record = run_activation_event(event, basin)
    assert record["atal_update"]["frustration"] > 0.5
    assert record["guard_decision"]["decision"] in ("HOLD", "WATCH")
    support_findings = [f for f in record["rigor_findings"] if f["analyzer"] == "claim_support"]
    assert support_findings[0]["state"] != "PASS"


def test_similarity_does_not_create_identity_link() -> None:
    """Similarity claim without identity evidence → WATCH/HOLD, not identity merge."""
    event = {
        "modality": "morphology",
        "source": "compare@local",
        "claim": "Trace B is identical to Trace A.",
        "content_summary": "Similar patterns asserted as same entity.",
        "similarity_claim": "branching_family_A",
        "identity_claim": "",
        "evidence": [],
        "supported": False,
        "risk_level": "medium",
    }
    findings = [f.to_dict() for f in run_rigor_checks(event)]
    sim = next(f for f in findings if f["analyzer"] == "similarity_vs_identity")
    assert sim["state"] in ("WATCH", "HOLD")
    guard = evaluate_guard(findings, event)
    assert guard.decision in ("WATCH", "HOLD")


def test_receptor_event_cannot_bypass_percept() -> None:
    """Receptor intake must produce PERCEPT-compatible event with intake provenance."""
    receptor = create_receptor_event(
        receptor_type="infinitysight_token",
        source="infinitysight@fieldnode",
        raw_summary="Visual token batch.",
        provenance={"layer": "mnmve"},
    )
    percept_event = to_percept_event(receptor)
    assert percept_event["provenance"]["intake_layer"] == "receptor_event"
    record = run_activation_event(percept_event, default_basin_state())
    assert "percept_token" in record
    assert record["percept_token"]["provenance"]["intake_layer"] == "receptor_event"


def test_fractal_memory_map_cannot_erase_contradiction_scars() -> None:
    """Adding contradiction link preserves both nodes and scores — no merge/delete."""
    fmm = FractalMemoryMap()
    fmm.add_node(FractalMemoryNode(node_id="x", label="X", source="a@local"))
    fmm.add_node(FractalMemoryNode(node_id="y", label="Y", source="b@local"))
    fmm.add_contradiction_link("x", "y")
    data = fmm.to_dict()
    assert "x" in data["nodes"]
    assert "y" in data["nodes"]
    assert data["nodes"]["x"]["contradiction_score"] > 0
    assert data["nodes"]["y"]["contradiction_score"] > 0
    contra_links = [l for l in data["links"] if l["relation_type"] == "contradiction"]
    assert len(contra_links) == 1

    mcva_hold = evaluate_gate(irregular_boundary())
    assert mcva_hold.decision == "HOLD"