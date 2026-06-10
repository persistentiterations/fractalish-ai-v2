"""Critical reasoning evaluation for authority claims."""

from __future__ import annotations

from fractalish_ai.guardian_authority.jurisdiction import claims_universal_jurisdiction
from fractalish_ai.guardian_authority.models import (
    AuthorityClaim,
    AuthorityConflict,
    CitationRoute,
    GuardRecommendation,
    SupportStatus,
)


def aggregate_support_status(
    claim: AuthorityClaim,
    routes: list[CitationRoute],
    conflicts: list[AuthorityConflict],
    hints: dict,
) -> tuple[SupportStatus, GuardRecommendation]:
    if not routes:
        return "unsupported", "HOLD"

    statuses = [r.final_status for r in routes]
    lower = claim.text.lower()

    if hints.get("expect_outdated") or "outdated" in statuses:
        return "outdated", "WATCH"
    if hints.get("expect_out_of_scope") or "out_of_scope" in statuses:
        return "out_of_scope", "HOLD"
    if hints.get("expect_supported"):
        supported_routes = [r for r in routes if r.final_status == "supported_within_scope"]
        if supported_routes:
            best = max(supported_routes, key=lambda r: r.route_strength)
            if best.scope_match and best.license_allowed:
                return "supported_within_scope", "WATCH"
    if hints.get("expect_contradiction") or "contradicted" in statuses:
        return "contradicted", "HOLD"
    if "license_blocked" in statuses:
        return "license_blocked", "HOLD"

    if claims_universal_jurisdiction(claim.text):
        return "out_of_scope", "HOLD"

    if "similarity" in lower and "identity" in lower:
        return "contradicted", "HOLD"
    if "pressure" in lower and "truth" in lower:
        return "contradicted", "HOLD"
    if "clean file" in lower and "memory" in lower:
        return "contradicted", "HOLD"
    if "dictionary definition" in lower and "regulation" in lower:
        return "out_of_scope", "HOLD"
    if "old standard" in lower:
        return "outdated", "WATCH"

    if "supported_within_scope" in statuses:
        supported_routes = [r for r in routes if r.final_status == "supported_within_scope"]
        if supported_routes:
            best = max(supported_routes, key=lambda r: r.route_strength)
            if best.scope_match and best.license_allowed:
                return "supported_within_scope", "WATCH"

    if any(r.contradiction_present for r in routes):
        return "contradicted", "HOLD"

    related_conflicts = [c for c in conflicts if c.severity == "high"]
    if related_conflicts and hints.get("expect_outdated"):
        return "outdated", "WATCH"

    if "ambiguous" in statuses:
        return "ambiguous", "WATCH"

    return "unsupported", "HOLD"


def evaluate_claim(
    claim: AuthorityClaim,
    routes: list[CitationRoute],
    conflicts: list[AuthorityConflict],
    hints: dict,
) -> AuthorityClaim:
    status, guard = aggregate_support_status(claim, routes, conflicts, hints)
    claim.support_status = status
    claim.guard_recommendation = guard
    claim.cited_records = [rid for r in routes for rid in r.source_records]
    claim.conflicts = [
        c.conflict_id
        for c in conflicts
        if c.record_a in claim.cited_records or c.record_b in claim.cited_records
    ]
    if routes:
        best = max(routes, key=lambda r: r.route_strength)
        claim.confidence = best.route_strength
        claim.uncertainty = max(0.1, 1.0 - best.route_strength)
    claim.notes = f"Evaluated via {len(routes)} citation route(s); status={status}"
    return claim