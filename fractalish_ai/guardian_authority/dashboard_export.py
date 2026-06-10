"""Dashboard summary export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_dashboard_summary(
    output_path: Path,
    *,
    sources: dict,
    records: dict,
    claims: dict,
    routes: list,
    conflicts: list,
    guard_decisions: list,
    lifecycle_records: list,
    audit_timeline: list,
) -> Path:
    payload: dict[str, Any] = {
        "authority_sources": [s.to_dict() for s in sources.values()],
        "authority_records": [r.to_dict() for r in records.values()],
        "authority_claims": [c.to_dict() for c in claims.values()],
        "citation_routes": [r.to_dict() for r in routes],
        "conflicts": [c.to_dict() for c in conflicts],
        "guard_decisions": guard_decisions,
        "lifecycle_records": [lr.to_dict() for lr in lifecycle_records],
        "hold_fog_claims": [
            c.to_dict() for c in claims.values() if c.support_status in ("hold", "contradicted", "unsupported", "out_of_scope")
        ],
        "audit_timeline": audit_timeline,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return output_path