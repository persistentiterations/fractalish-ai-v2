"""Core runtime — wires PERCEPT, ATAL, RIGOR, CIRCUIT, GUARD, SERA, SessionGlyph."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from typing import Any

from fractalish_ai.atal import AtalState, update_atal
from fractalish_ai.circuit import CircuitState, circuit_from_dict, update_circuit
from fractalish_ai.guard import evaluate_guard
from fractalish_ai.percept import create_percept
from fractalish_ai.rigor import run_rigor_checks
from fractalish_ai.sera import SeraTimer, build_sera_record
from fractalish_ai.session_glyph import SessionGlyph, build_session_glyph


def default_basin_state() -> dict[str, Any]:
    return {
        "atal": asdict(AtalState()),
        "circuit": CircuitState().to_dict(),
        "activation_id": str(uuid.uuid4()),
        "purpose": "",
        "operator_constraints": [],
    }


def run_activation_event(event: dict[str, Any], basin_state: dict[str, Any] | None = None) -> dict[str, Any]:
    timer = SeraTimer()
    basin = basin_state or default_basin_state()

    percept = create_percept(
        modality=event.get("modality", "text"),
        source=event.get("source", ""),
        content_summary=event.get("content_summary") or event.get("claim", ""),
        raw_reference=event.get("raw_reference", ""),
        confidence=float(event.get("confidence", 0.5)),
        uncertainty=event.get("uncertainty"),
        provenance=event.get("provenance", {}),
        domain_tags=event.get("domain_tags", []),
        event_id=event.get("event_id"),
    )

    atal = AtalState(**basin.get("atal", {}))
    circuit_data = basin.get("circuit", {})
    event_payload = dict(event)
    event_payload["prior_unresolved_hold_count"] = len(circuit_data.get("unresolved_holds", []))
    rigor_findings = [f.to_dict() for f in run_rigor_checks(event_payload)]
    guard = evaluate_guard(rigor_findings, event)

    boundary_violation = bool(event.get("boundary_violation"))
    atal = update_atal(
        atal,
        confidence=percept.confidence,
        uncertainty=percept.uncertainty,
        hold_count=sum(1 for f in rigor_findings if f["state"] == "HOLD"),
        contradiction_count=sum(1 for f in rigor_findings if f["analyzer"] == "contradiction" and f["state"] != "PASS"),
        boundary_violation=boundary_violation,
    )

    circuit = circuit_from_dict(circuit_data)

    circuit_updates = update_circuit(
        circuit,
        percept=percept.to_dict(),
        rigor_findings=rigor_findings,
        guard_decision=guard.decision,
    )

    purpose = basin.get("purpose") or event.get("purpose", "bounded activation")
    glyph = build_session_glyph(
        activation_id=basin.get("activation_id", str(uuid.uuid4())),
        purpose=purpose,
        operator_constraints=basin.get("operator_constraints", []),
        circuit=circuit.to_dict(),
        guard_decision=guard.decision,
        key_sources=[percept.source] if percept.source else [],
    )

    sera = build_sera_record(
        runtime_ms=timer.elapsed_ms(),
        input_payload=event,
        output_payload=glyph.to_dict(),
        rigor_findings=rigor_findings,
        guard_decision=guard.decision,
        memory_delta=event.get("memory_delta"),
    )

    updated_basin = {
        "activation_id": glyph.activation_id,
        "purpose": purpose,
        "operator_constraints": basin.get("operator_constraints", []),
        "atal": atal.to_dict(),
        "circuit": circuit.to_dict(),
        "session_glyph": glyph.to_dict(),
    }

    return {
        "event_id": percept.event_id,
        "percept_token": percept.to_dict(),
        "atal_update": atal.to_dict(),
        "rigor_findings": rigor_findings,
        "circuit_updates": circuit_updates,
        "guard_decision": guard.to_dict(),
        "sera_record": sera.to_dict(),
        "updated_session_glyph": glyph.to_dict(),
        "updated_basin_state": updated_basin,
    }


def export_decision_record(path: str, record: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, default=str)