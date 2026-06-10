"""ReceptorEvent → PERCEPT contract tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.basin_link import BasinLink, bind_receptor_to_basin, receptor_event_to_decision_record
from fractalish_ai.receptors import ReceptorType, create_receptor_event, to_percept_event


def test_receptor_event_converts_to_percept() -> None:
    receptor = create_receptor_event(
        receptor_type=ReceptorType.HUMAN_NOTE,
        source="operator@field",
        raw_summary="Note for basin intake.",
        possible_claims=["Preliminary observation pending review."],
        missing_context=["source_document"],
    )
    percept_event = to_percept_event(receptor)
    assert percept_event["modality"] == receptor.modality
    assert percept_event["source"] == receptor.source
    assert percept_event["content_summary"] == receptor.raw_summary
    assert percept_event["provenance"]["receptor_type"] == "human_note"
    assert percept_event["provenance"]["intake_layer"] == "receptor_event"
    assert percept_event["supported"] is False
    assert "guard_decision" not in percept_event


def test_receptor_event_does_not_set_guard() -> None:
    receptor = create_receptor_event(
        receptor_type=ReceptorType.HUMAN_NOTE,
        source="operator@field",
        raw_summary="Must not auto-proceed.",
        possible_claims=["This proves intelligence."],
    )
    record = receptor_event_to_decision_record(receptor)
    assert "guard_decision" in record
    assert record["guard_decision"]["decision"] in ("PROCEED", "HOLD", "WATCH", "REVERSE")
    assert record["receptor_event"]["receptor_type"] == "human_note"
    assert record["percept_input_event"]["supported"] is False


def test_basin_link_preserves_activation_id() -> None:
    activation_id = "act-preserve-001"
    receptor = create_receptor_event(
        receptor_type=ReceptorType.HUMAN_NOTE,
        source="operator@field",
        raw_summary="Continuity test.",
    )
    link = BasinLink(
        activation_id=activation_id,
        purpose="contract test",
        operator_constraints=["local_only"],
    )
    percept_event, updated = bind_receptor_to_basin(receptor, link)
    assert updated.activation_id == activation_id
    record = receptor_event_to_decision_record(receptor, updated)
    assert record["updated_session_glyph"]["activation_id"] == activation_id
    assert record["basin_link"]["activation_id"] == activation_id
    assert percept_event["purpose"] == "contract test"