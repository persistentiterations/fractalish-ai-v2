"""PERCEPT — structured percept tokens from incoming events."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class PerceptToken:
    event_id: str
    modality: str
    source: str
    timestamp: str
    content_summary: str
    raw_reference: str
    confidence: float
    uncertainty: float
    provenance: dict[str, Any]
    domain_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def create_percept(
    *,
    modality: str,
    source: str,
    content_summary: str,
    raw_reference: str = "",
    confidence: float = 0.5,
    uncertainty: float | None = None,
    provenance: dict[str, Any] | None = None,
    domain_tags: list[str] | None = None,
    event_id: str | None = None,
) -> PerceptToken:
    if uncertainty is None:
        uncertainty = max(0.0, 1.0 - confidence)
    return PerceptToken(
        event_id=event_id or str(uuid.uuid4()),
        modality=modality,
        source=source,
        timestamp=datetime.now(timezone.utc).isoformat(),
        content_summary=content_summary,
        raw_reference=raw_reference,
        confidence=max(0.0, min(1.0, confidence)),
        uncertainty=max(0.0, min(1.0, uncertainty)),
        provenance=provenance or {},
        domain_tags=domain_tags or [],
    )