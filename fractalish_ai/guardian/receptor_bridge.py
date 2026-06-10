"""GuardianReceptorBridge — Guardian intake → ReceptorEvent."""

from __future__ import annotations

from fractalish_ai.guardian.models import (
    GuardianDecision,
    GuardianIntakeEvent,
    GuardianLifecycleRecord,
    GuardianSanitizedArtifact,
    GuardianScanReport,
)
from fractalish_ai.receptors import ReceptorEvent, ReceptorType, create_receptor_event


CHANNEL_TO_RECEPTOR: dict[str, ReceptorType] = {
    "file_drop": ReceptorType.GUARDIAN_FILE,
    "local_file_drop": ReceptorType.GUARDIAN_LOCAL_DROP,
    "local_drop": ReceptorType.GUARDIAN_LOCAL_DROP,
    "email": ReceptorType.GUARDIAN_EMAIL,
    "email_mock": ReceptorType.GUARDIAN_EMAIL,
    "mcp": ReceptorType.GUARDIAN_MCP_RESOURCE,
    "mcp_resource": ReceptorType.GUARDIAN_MCP_RESOURCE,
    "browser": ReceptorType.GUARDIAN_BROWSER_CAPTURE,
    "browser_capture_mock": ReceptorType.GUARDIAN_BROWSER_CAPTURE,
    "basinmail": ReceptorType.BASINMAIL_MESSAGE,
}


def bridge_to_receptor(
    intake: GuardianIntakeEvent,
    scan: GuardianScanReport,
    sanitized: GuardianSanitizedArtifact,
    lifecycle: GuardianLifecycleRecord,
    decision: GuardianDecision,
    receptor_type: ReceptorType | None = None,
) -> ReceptorEvent:
    rtype = receptor_type or CHANNEL_TO_RECEPTOR.get(intake.source_channel, ReceptorType.GUARDIAN_FILE)
    risk_map = {"LOW": "low", "MEDIUM": "medium", "HIGH": "high", "CRITICAL": "critical"}

    receptor = create_receptor_event(
        receptor_type=rtype,
        source=f"guardian@{intake.source_identity}",
        raw_summary=sanitized.visible_text_summary[:500] or sanitized.model_visible_representation[:500],
        modality="guardian_sanitized_intake",
        raw_reference=intake.intake_id,
        confidence=scan.confidence,
        uncertainty=scan.uncertainty,
        provenance={
            "guardian_intake_id": intake.intake_id,
            "guardian_decision": decision.decision,
            "guardian_risk_level": risk_map.get(scan.risk_level, "medium"),
            "guardian_risk_score": scan.risk_score,
            "guardian_scan_status": scan.scan_status,
            "lifecycle_state": lifecycle.lifecycle_state,
            "allowed_representations": decision.allowed_representations,
            "raw_model_visible": scan.raw_model_visible,
            "sanitized_model_visible": scan.sanitized_model_visible,
            "reason_codes": scan.reason_codes,
            "sha256": intake.sha256,
            "source_channel": intake.source_channel,
            "intake_layer": "guardian_receptor_bridge",
        },
        domain_tags=["guardian", "intake", intake.source_channel],
        possible_claims=[sanitized.visible_text_summary[:200]] if sanitized.visible_text_summary else [],
        missing_context=scan.reason_codes if scan.risk_level in ("HIGH", "CRITICAL") else [],
        normalized_payload={
            "model_visible_representation": sanitized.model_visible_representation,
            "unsafe_instruction_summary": sanitized.unsafe_instruction_summary,
            "flagged_segments": sanitized.removed_or_flagged_segments[:20],
            "prompt_injection_flags": scan.prompt_injection_flags,
            "tool_poisoning_flags": scan.tool_poisoning_flags,
        },
        event_id=intake.intake_id,
    )
    receptor.receptor_notes = "Guardian-sanitized intake — evidence not truth; raw not model-visible by default"
    return receptor