"""Guardian Intake Gateway data models."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

LifecycleState = Literal[
    "RECEIVED", "QUARANTINED", "SCANNING", "SANITIZED", "MODEL_VISIBLE",
    "LIMITED_EXPOSURE", "HOLD", "HUMAN_REVIEW", "REJECTED", "EXPIRED",
    "PURGE_PENDING", "PURGED",
]

GuardianDecisionState = Literal[
    "PROCEED", "WATCH", "HOLD", "REVERSE", "SANITIZED_ONLY",
    "METADATA_ONLY", "HUMAN_REVIEW_REQUIRED", "PURGE_OR_EXPIRE",
]

RiskLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]


@dataclass
class GuardianIntakeEvent:
    intake_id: str
    activation_id: str
    session_id: str
    source_channel: str
    source_identity: str
    received_at: str
    raw_path: str
    declared_mime_type: str
    detected_mime_type: str
    file_name: str
    size_bytes: int
    sha256: str
    raw_available: bool
    quarantine_path: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GuardianScanReport:
    intake_id: str
    scan_status: str
    malware_stub_status: str = "not_run"
    file_type_status: str = "ok"
    archive_status: str = "not_archive"
    macro_status: str = "not_applicable"
    link_status: str = "none"
    prompt_injection_flags: list[str] = field(default_factory=list)
    hidden_instruction_flags: list[str] = field(default_factory=list)
    tool_poisoning_flags: list[str] = field(default_factory=list)
    suspicious_patterns: list[str] = field(default_factory=list)
    dlp_flags: list[str] = field(default_factory=list)
    risk_score: int = 0
    risk_level: RiskLevel = "LOW"
    confidence: float = 0.7
    uncertainty: float = 0.3
    reason_codes: list[str] = field(default_factory=list)
    safe_to_summarize: bool = True
    raw_model_visible: bool = False
    sanitized_model_visible: bool = True
    metadata_only: bool = False
    human_review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GuardianSanitizedArtifact:
    intake_id: str
    sanitized_id: str
    sanitized_path: str
    sanitized_text: str
    removed_or_flagged_segments: list[str] = field(default_factory=list)
    visible_text_summary: str = ""
    unsafe_instruction_summary: str = ""
    model_visible_representation: str = ""
    allowed_representations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GuardianLifecycleRecord:
    artifact_id: str
    intake_id: str
    activation_id: str
    session_id: str
    owner: str
    privacy_scope: str
    lifecycle_state: LifecycleState
    retention_policy: str
    expires_at: str
    legal_hold: bool
    purge_allowed: bool
    purge_requested_at: str = ""
    purge_completed_at: str = ""
    derivative_artifacts: dict[str, str] = field(default_factory=dict)
    audit_log_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GuardianDecision:
    intake_id: str
    decision: GuardianDecisionState
    reason_codes: list[str]
    blocked_content_types: list[str] = field(default_factory=list)
    allowed_representations: list[str] = field(default_factory=list)
    requires_operator_review: bool = False
    expires_at: str = ""
    policy_version: str = "v0.1"
    decision_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def finalize(self) -> GuardianDecision:
        payload = f"{self.intake_id}:{self.decision}:{','.join(self.reason_codes)}"
        self.decision_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self


@dataclass
class GuardianAuditRecord:
    audit_id: str
    intake_id: str
    timestamp: str
    action: str
    actor: str
    before_state: str
    after_state: str
    reason: str
    hash_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_intake_id() -> str:
    return f"gintake-{uuid.uuid4().hex[:12]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()