"""Guardian Authority Corpus data models."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

SourceType = Literal[
    "dictionary", "encyclopedia", "government_rule", "regulation", "statute",
    "technical_standard", "stem_reference", "manual", "internal_policy", "mock_reference",
]
AuthorityLevel = Literal[
    "lexical", "educational", "governmental", "regulatory", "statutory",
    "technical_standard", "internal", "unknown", "mock",
]
LicenseStatus = Literal[
    "public_domain", "open_license", "paid_api_required",
    "proprietary_restricted", "mock_only", "unknown",
]
RecordType = Literal[
    "definition", "encyclopedia_summary", "rule_excerpt", "regulation_excerpt",
    "standard_excerpt", "manual_instruction", "formula", "glossary",
    "policy_clause", "mock_entry",
]
ClaimType = Literal[
    "definition_claim", "factual_claim", "procedural_claim", "regulatory_claim",
    "standard_claim", "scope_claim", "exception_claim", "version_claim",
    "unsupported_user_claim",
]
SupportStatus = Literal[
    "supported_within_scope", "unsupported", "contradicted", "ambiguous",
    "out_of_scope", "outdated", "license_blocked", "hold",
]
RouteType = Literal[
    "direct_definition", "direct_rule", "direct_standard", "analogy",
    "cross_reference", "unsupported", "conflict_route",
]
ConflictType = Literal[
    "direct_contradiction", "version_conflict", "jurisdiction_conflict",
    "definition_conflict", "scope_conflict", "license_conflict", "ambiguity",
]
GuardRecommendation = Literal["PROCEED", "WATCH", "HOLD", "REVERSE"]
LifecycleState = Literal[
    "INGESTED", "INDEXED", "EVALUATED", "HOLD", "PURGE_PENDING", "PURGED",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class AuthoritySource:
    source_id: str
    source_name: str
    source_type: SourceType
    publisher: str
    authority_level: AuthorityLevel
    jurisdiction: str
    domain: str
    license_status: LicenseStatus
    license_notes: str = ""
    access_method: str = "local_file"
    version: str = "1.0"
    effective_date: str = ""
    retrieved_at: str = ""
    provenance_url_or_reference: str = ""
    trust_scope: str = ""
    limitations: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorityRecord:
    record_id: str
    source_id: str
    title: str
    record_type: RecordType
    text: str
    normalized_text: str = ""
    key_terms: list[str] = field(default_factory=list)
    definitions: dict[str, str] = field(default_factory=dict)
    claims: list[str] = field(default_factory=list)
    scope: str = ""
    jurisdiction: str = ""
    version: str = "1.0"
    effective_date: str = ""
    expiration_date: str = ""
    supersedes: str = ""
    superseded_by: str = ""
    citation: str = ""
    license_status: LicenseStatus = "mock_only"
    confidence: float = 0.7
    uncertainty: float = 0.3
    notes: str = ""
    supports_user_claims: list[str] = field(default_factory=list)
    contradicts_user_claims: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorityClaim:
    claim_id: str
    text: str
    claim_type: ClaimType
    source_record_id: str = ""
    source_id: str = ""
    scope: str = ""
    jurisdiction: str = ""
    version: str = ""
    confidence: float = 0.5
    uncertainty: float = 0.5
    dependency_terms: list[str] = field(default_factory=list)
    cited_records: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    support_status: SupportStatus = "unsupported"
    guard_recommendation: GuardRecommendation = "HOLD"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CitationRoute:
    route_id: str
    claim_id: str
    source_records: list[str]
    route_type: RouteType
    route_strength: float
    scope_match: bool
    jurisdiction_match: bool
    version_match: bool
    license_allowed: bool
    contradiction_present: bool
    missing_dependencies: list[str] = field(default_factory=list)
    final_status: SupportStatus = "unsupported"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorityConflict:
    conflict_id: str
    record_a: str
    record_b: str
    claim_a: str
    claim_b: str
    conflict_type: ConflictType
    severity: str
    scope_notes: str = ""
    jurisdiction_notes: str = ""
    version_notes: str = ""
    resolution_status: str = "unresolved"
    guard_recommendation: GuardRecommendation = "HOLD"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorityReceptorEvent:
    event_id: str
    activation_id: str
    session_id: str
    receptor_type: str
    source_channel: str
    authority_source: dict[str, Any]
    authority_record: dict[str, Any]
    authority_claims: list[dict[str, Any]]
    citation_routes: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    provenance: dict[str, Any]
    license_status: str
    jurisdiction: str
    version: str
    confidence: float
    uncertainty: float
    possible_claims: list[str]
    missing_context: list[str]
    guard_recommendation: str
    lifecycle_state: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuthorityLifecycleRecord:
    artifact_id: str
    source_id: str
    record_ids: list[str]
    lifecycle_state: LifecycleState
    retention_policy: str
    expires_at: str
    purge_allowed: bool
    derivative_artifacts: dict[str, str] = field(default_factory=dict)
    audit_log_reference: str = ""
    purge_completed_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)