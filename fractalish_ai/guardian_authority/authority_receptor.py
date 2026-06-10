"""AuthorityReceptorEvent bridge to base ReceptorEvent."""

from __future__ import annotations

from typing import Any

from fractalish_ai.guardian_authority.models import (
    AuthorityClaim,
    AuthorityConflict,
    AuthorityRecord,
    AuthorityReceptorEvent,
    AuthoritySource,
    CitationRoute,
)
from fractalish_ai.receptors import ReceptorEvent, ReceptorType, create_receptor_event

SOURCE_TYPE_TO_RECEPTOR: dict[str, ReceptorType] = {
    "dictionary": ReceptorType.AUTHORITY_DICTIONARY,
    "encyclopedia": ReceptorType.AUTHORITY_ENCYCLOPEDIA,
    "government_rule": ReceptorType.AUTHORITY_GOVERNMENT_RULE,
    "regulation": ReceptorType.AUTHORITY_REGULATION,
    "statute": ReceptorType.AUTHORITY_REGULATION,
    "technical_standard": ReceptorType.AUTHORITY_STANDARD,
    "stem_reference": ReceptorType.AUTHORITY_STEM_REFERENCE,
    "manual": ReceptorType.AUTHORITY_MANUAL,
    "internal_policy": ReceptorType.AUTHORITY_MOCK_REFERENCE,
    "mock_reference": ReceptorType.AUTHORITY_MOCK_REFERENCE,
}


def build_authority_receptor_event(
    *,
    event_id: str,
    activation_id: str,
    session_id: str,
    source: AuthoritySource,
    record: AuthorityRecord | None,
    claim: AuthorityClaim,
    routes: list[CitationRoute],
    conflicts: list[AuthorityConflict],
    lifecycle_state: str = "EVALUATED",
) -> AuthorityReceptorEvent:
    rtype = SOURCE_TYPE_TO_RECEPTOR.get(source.source_type, ReceptorType.AUTHORITY_MOCK_REFERENCE)
    missing = list(claim.conflicts)
    if claim.support_status in ("unsupported", "out_of_scope", "outdated"):
        missing.append(claim.support_status)
    for route in routes:
        missing.extend(route.missing_dependencies)

    return AuthorityReceptorEvent(
        event_id=event_id,
        activation_id=activation_id,
        session_id=session_id,
        receptor_type=rtype.value,
        source_channel="authority_corpus",
        authority_source=source.to_dict(),
        authority_record=record.to_dict() if record else {},
        authority_claims=[claim.to_dict()],
        citation_routes=[r.to_dict() for r in routes],
        conflicts=[c.to_dict() for c in conflicts[:10]],
        provenance={
            "authority_source_id": source.source_id,
            "authority_record_id": record.record_id if record else "",
            "claim_id": claim.claim_id,
            "support_status": claim.support_status,
            "intake_layer": "guardian_authority_corpus",
            "governed_reference": True,
            "automatic_truth": False,
        },
        license_status=source.license_status,
        jurisdiction=claim.jurisdiction or source.jurisdiction,
        version=record.version if record else source.version,
        confidence=claim.confidence,
        uncertainty=claim.uncertainty,
        possible_claims=[claim.text],
        missing_context=sorted(set(missing)),
        guard_recommendation=claim.guard_recommendation,
        lifecycle_state=lifecycle_state,
        notes="Authority evidence — not automatic truth; RIGOR/GUARD must evaluate",
    )


def to_base_receptor_event(auth_event: AuthorityReceptorEvent) -> ReceptorEvent:
    risk_map = {
        "PROCEED": "low",
        "WATCH": "medium",
        "HOLD": "high",
        "REVERSE": "critical",
    }
    receptor = create_receptor_event(
        receptor_type=auth_event.receptor_type,
        source=f"authority@{auth_event.authority_source.get('source_name', 'corpus')}",
        raw_summary=auth_event.possible_claims[0] if auth_event.possible_claims else "",
        modality="authority_governed_reference",
        raw_reference=auth_event.event_id,
        confidence=auth_event.confidence,
        uncertainty=auth_event.uncertainty,
        provenance={
            **auth_event.provenance,
            "guardian_authority_decision": auth_event.guard_recommendation,
            "guardian_risk_level": risk_map.get(auth_event.guard_recommendation, "medium"),
            "license_status": auth_event.license_status,
            "jurisdiction": auth_event.jurisdiction,
            "version": auth_event.version,
            "lifecycle_state": auth_event.lifecycle_state,
            "support_status": auth_event.provenance.get("support_status"),
            "citation_route_count": len(auth_event.citation_routes),
        },
        domain_tags=["authority", "governed_reference", auth_event.source_channel],
        possible_claims=auth_event.possible_claims,
        missing_context=auth_event.missing_context,
        normalized_payload={
            "authority_claims": auth_event.authority_claims,
            "citation_routes": auth_event.citation_routes,
            "conflicts": auth_event.conflicts,
            "guard_recommendation": auth_event.guard_recommendation,
        },
        event_id=auth_event.event_id,
    )
    receptor.receptor_notes = auth_event.notes
    return receptor