"""ReceptorEvent — structured intake upstream of PERCEPT (not truth, not GUARD)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReceptorType(str, Enum):
    HUMAN_NOTE = "human_note"
    FILE_DROP = "file_drop"
    MAZE_TRACE = "maze_trace"
    NATURAL_MATH_RUN = "natural_math_run"
    MORPHOLOGY_TRACE = "morphology_trace"
    SENSOR_STUB = "sensor_stub"
    MULTIMODAL_STUB = "multimodal_stub"
    INFINITYSIGHT_TOKEN = "infinitysight_token"
    GUARDIAN_FILE = "guardian_file"
    GUARDIAN_EMAIL = "guardian_email"
    GUARDIAN_MCP_RESOURCE = "guardian_mcp_resource"
    GUARDIAN_BROWSER_CAPTURE = "guardian_browser_capture"
    GUARDIAN_LOCAL_DROP = "guardian_local_drop"
    BASINMAIL_MESSAGE = "basinmail_message"
    BASINMAIL_ATTACHMENT = "basinmail_attachment"
    AUTHORITY_DICTIONARY = "authority_dictionary"
    AUTHORITY_ENCYCLOPEDIA = "authority_encyclopedia"
    AUTHORITY_GOVERNMENT_RULE = "authority_government_rule"
    AUTHORITY_REGULATION = "authority_regulation"
    AUTHORITY_STANDARD = "authority_standard"
    AUTHORITY_STEM_REFERENCE = "authority_stem_reference"
    AUTHORITY_MANUAL = "authority_manual"
    AUTHORITY_MOCK_REFERENCE = "authority_mock_reference"


@dataclass
class ReceptorEvent:
    receptor_id: str
    receptor_type: str
    event_id: str
    timestamp: str
    source: str
    modality: str
    raw_reference: str
    raw_summary: str
    normalized_payload: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    uncertainty: float = 0.5
    noise_estimate: float = 0.0
    provenance: dict[str, Any] = field(default_factory=dict)
    domain_tags: list[str] = field(default_factory=list)
    privacy_scope: str = "local"
    local_only: bool = True
    suggested_basin_tags: list[str] = field(default_factory=list)
    possible_claims: list[str] = field(default_factory=list)
    missing_context: list[str] = field(default_factory=list)
    receptor_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_receptor_event(
    *,
    receptor_type: str | ReceptorType,
    source: str,
    raw_summary: str,
    modality: str = "receptor_intake",
    raw_reference: str = "",
    confidence: float = 0.5,
    uncertainty: float | None = None,
    provenance: dict[str, Any] | None = None,
    domain_tags: list[str] | None = None,
    possible_claims: list[str] | None = None,
    missing_context: list[str] | None = None,
    normalized_payload: dict[str, Any] | None = None,
    receptor_id: str | None = None,
    event_id: str | None = None,
) -> ReceptorEvent:
    rtype = receptor_type.value if isinstance(receptor_type, ReceptorType) else receptor_type
    if uncertainty is None:
        uncertainty = max(0.0, 1.0 - confidence)
    return ReceptorEvent(
        receptor_id=receptor_id or str(uuid.uuid4()),
        receptor_type=rtype,
        event_id=event_id or str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        source=source,
        modality=modality,
        raw_reference=raw_reference,
        raw_summary=raw_summary,
        normalized_payload=normalized_payload or {},
        confidence=max(0.0, min(1.0, confidence)),
        uncertainty=max(0.0, min(1.0, uncertainty)),
        provenance=provenance or {},
        domain_tags=domain_tags or [],
        local_only=True,
        possible_claims=possible_claims or [],
        missing_context=missing_context or [],
        receptor_notes="intake only — does not decide truth or GUARD",
    )


def to_percept_event(receptor: ReceptorEvent) -> dict[str, Any]:
    """Convert ReceptorEvent to PERCEPT-compatible activation event dict.

    Does not set supported=True, guard, or truth decisions.
    possible_claims are candidates for RIGOR — not accepted facts.
    """
    claim = receptor.possible_claims[0] if receptor.possible_claims else receptor.raw_summary
    return {
        "event_id": receptor.event_id,
        "modality": receptor.modality,
        "source": receptor.source,
        "content_summary": receptor.raw_summary,
        "claim": claim,
        "raw_reference": receptor.raw_reference,
        "confidence": receptor.confidence,
        "uncertainty": receptor.uncertainty,
        "provenance": {
            **receptor.provenance,
            "receptor_id": receptor.receptor_id,
            "receptor_type": receptor.receptor_type,
            "intake_layer": "receptor_event",
            "local_only": receptor.local_only,
            "privacy_scope": receptor.privacy_scope,
        },
        "domain_tags": list(receptor.domain_tags),
        "evidence": [],
        "supported": False,
        "risk_level": receptor.provenance.get("guardian_risk_level", "low"),
        "speculation": bool(receptor.missing_context),
        "receptor_normalized_payload": receptor.normalized_payload,
        "receptor_possible_claims": list(receptor.possible_claims),
        "receptor_missing_context": list(receptor.missing_context),
        "receptor_notes": receptor.receptor_notes,
    }