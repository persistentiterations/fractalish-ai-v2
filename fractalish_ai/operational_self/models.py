"""Operational Self + Fractal Attractor Memory data models."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

BasinRegion = Literal[
    "core", "active", "near", "peripheral", "dormant", "fog", "scar", "archived", "purged",
]
AttractorStatus = Literal["active", "watch", "hold", "scarred", "deprecated", "archived", "purged"]
CompressionLevel = Literal["none", "light", "medium"]
ScarStatus = Literal["unresolved", "resolved", "superseded", "watch", "hold"]
SourceType = Literal[
    "chat_turn", "chat_session", "file_upload", "guardian_intake", "guardian_authority",
    "cognitive_basin_run", "natural_math_run", "mcva_readout", "system_decision",
    "operator_note", "external_artifact", "mock_event",
]
LinkType = Literal[
    "supports", "contradicts", "elaborates", "depends_on", "replaces", "supersedes",
    "resembles", "analogy", "recovery_route", "same_project", "same_claim",
    "same_source", "operator_anchor", "authority_route", "guardian_route", "session_continuity",
]

DEFAULT_NON_CLAIMS = [
    "no consciousness claim",
    "no sentience claim",
    "no subjective experience claim",
    "no legal personhood claim",
    "no life claim",
    "no autonomy claim beyond bounded activation behavior",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def state_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


@dataclass
class OperationalSelfState:
    self_id: str
    activation_id: str
    project_id: str
    purpose: str
    operator_constraints: list[str] = field(default_factory=list)
    active_narrative: str = ""
    active_focus: str = ""
    current_phase: str = "building"
    core_commitments: list[str] = field(default_factory=list)
    unresolved_loops: list[str] = field(default_factory=list)
    contradiction_scars: list[str] = field(default_factory=list)
    hold_regions: list[str] = field(default_factory=list)
    recovery_routes: list[str] = field(default_factory=list)
    active_attractors: list[str] = field(default_factory=list)
    deprioritized_memories: list[str] = field(default_factory=list)
    recent_memory_ids: list[str] = field(default_factory=list)
    session_glyph_refs: list[str] = field(default_factory=list)
    last_updated: str = ""
    confidence: float = 0.7
    uncertainty: float = 0.3
    non_claims: list[str] = field(default_factory=lambda: list(DEFAULT_NON_CLAIMS))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryEvent:
    event_id: str
    activation_id: str
    source_type: SourceType
    source_id: str
    timestamp: str
    raw_summary: str
    structured_summary: str = ""
    claims: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    guard_status: str = "WATCH"
    atal_pressure: float = 0.0
    rigor_status: str = "unchecked"
    sera_cost: float = 0.0
    emotional_or_pressure_load: float = 0.0
    provenance: dict[str, Any] = field(default_factory=dict)
    operator_notes: str = ""
    tags: list[str] = field(default_factory=list)
    confidence: float = 0.5
    uncertainty: float = 0.5
    importance_hint: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompressedMemory:
    memory_id: str
    source_event_id: str
    activation_id: str
    compression_level: CompressionLevel = "light"
    compressed_summary: str = ""
    retained_claims: list[str] = field(default_factory=list)
    retained_decisions: list[str] = field(default_factory=list)
    retained_constraints: list[str] = field(default_factory=list)
    retained_open_loops: list[str] = field(default_factory=list)
    retained_scars: list[str] = field(default_factory=list)
    retained_routes: list[str] = field(default_factory=list)
    dropped_noise: list[str] = field(default_factory=list)
    compression_notes: str = ""
    lossiness: float = 0.1
    replay_fidelity_estimate: float = 0.9
    confidence: float = 0.7
    uncertainty: float = 0.3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryAttractor:
    attractor_id: str
    memory_id: str
    label: str
    salience_score: float = 0.5
    centrality_score: float = 0.5
    recurrence_score: float = 0.0
    utility_score: float = 0.5
    contradiction_score: float = 0.0
    pressure_score: float = 0.0
    authority_score: float = 0.0
    recency_score: float = 0.5
    replay_value: float = 0.0
    distance_from_reasoning_center: float = 0.5
    basin_region: BasinRegion = "near"
    links: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    status: AttractorStatus = "active"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryLink:
    link_id: str
    from_memory_id: str
    to_memory_id: str
    link_type: LinkType
    strength: float = 0.5
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.7
    uncertainty: float = 0.3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContradictionScar:
    scar_id: str
    memory_ids: list[str]
    claim_a: str
    claim_b: str
    severity: str = "medium"
    first_seen: str = ""
    last_seen: str = ""
    status: ScarStatus = "unresolved"
    guard_effect: str = "HOLD"
    replay_warning: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FogRegion:
    fog_id: str
    label: str
    related_memory_ids: list[str]
    reason: str
    missing_context: list[str] = field(default_factory=list)
    guard_status: str = "HOLD"
    created_at: str = ""
    review_needed: bool = True
    next_action: str = "Gather missing context before closure."

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReplayRoute:
    route_id: str
    label: str
    start_memory_id: str
    target_memory_id: str
    memory_path: list[str]
    required_context: list[str] = field(default_factory=list)
    unresolved_holds: list[str] = field(default_factory=list)
    contradiction_warnings: list[str] = field(default_factory=list)
    recommended_next_action: str = ""
    confidence: float = 0.7
    uncertainty: float = 0.3

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelfNarrativeFrame:
    frame_id: str
    activation_id: str
    narrative_summary: str
    current_identity_sentence: str
    current_project_state: str
    current_product_state: str
    active_doctrines: list[str] = field(default_factory=list)
    active_constraints: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    active_risks: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OperationalSelfSnapshot:
    snapshot_id: str
    self_state: dict[str, Any]
    narrative_frame: dict[str, Any]
    core_attractors: list[dict[str, Any]]
    active_attractors: list[dict[str, Any]]
    fog_regions: list[dict[str, Any]]
    contradiction_scars: list[dict[str, Any]]
    replay_routes: list[dict[str, Any]]
    memory_counts: dict[str, int]
    integrity_warnings: list[str]
    created_at: str
    state_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def finalize(self) -> OperationalSelfSnapshot:
        self.state_hash = state_hash(
            {
                "self_state": self.self_state,
                "narrative_frame": self.narrative_frame,
                "memory_counts": self.memory_counts,
            }
        )
        return self