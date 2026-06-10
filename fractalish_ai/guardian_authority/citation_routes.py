"""Citation route construction and evaluation."""

from __future__ import annotations

from fractalish_ai.guardian_authority.jurisdiction import jurisdiction_match
from fractalish_ai.guardian_authority.licensing import license_status_for_route
from fractalish_ai.guardian_authority.models import (
    AuthorityClaim,
    AuthorityRecord,
    AuthoritySource,
    CitationRoute,
    SupportStatus,
    new_id,
)
from fractalish_ai.guardian_authority.versioning import is_outdated, version_match

RECORD_TYPE_TO_ROUTE = {
    "definition": "direct_definition",
    "glossary": "direct_definition",
    "rule_excerpt": "direct_rule",
    "regulation_excerpt": "direct_rule",
    "standard_excerpt": "direct_standard",
    "manual_instruction": "direct_standard",
    "encyclopedia_summary": "cross_reference",
    "policy_clause": "direct_rule",
    "formula": "direct_standard",
    "mock_entry": "cross_reference",
}


def scope_match(record: AuthorityRecord, required_scope: str = "", claim_text: str = "") -> bool:
    rec_scope = record.scope.lower()
    if "dictionary" in claim_text.lower() and "regulation" in claim_text.lower():
        if rec_scope in ("lexical", "educational", "dictionary", "glossary"):
            return False
        if record.record_type in ("definition", "glossary"):
            return False
    if not required_scope:
        return True
    req = required_scope.lower()
    if req == "regulatory" and rec_scope in ("lexical", "educational", "dictionary"):
        return False
    if req == "scoped_authority" and rec_scope in ("scoped_authority", "general", "authority_reasoning"):
        return True
    if req == "guardian_intake" and rec_scope in ("guardian_intake", "ai_safety", "lifecycle"):
        return True
    return req in rec_scope or rec_scope in req or rec_scope == "general"


def build_route(
    claim: AuthorityClaim,
    record: AuthorityRecord,
    source: AuthoritySource,
    *,
    match_score: float,
    hints: dict,
) -> CitationRoute:
    rtype = RECORD_TYPE_TO_ROUTE.get(record.record_type, "cross_reference")  # type: ignore[assignment]
    scope_ok = scope_match(record, hints.get("required_scope", ""), claim.text)
    juris_ok = jurisdiction_match(record.jurisdiction, hints.get("required_jurisdiction", claim.jurisdiction))
    if hints.get("expect_out_of_scope") and claim.text.lower().count("everywhere"):
        if record.jurisdiction not in ("universal", "global", ""):
            juris_ok = False
    version_ok = version_match(record, hints.get("required_version", ""))
    if hints.get("expect_outdated") and is_outdated(record):
        version_ok = False
    license_ok = license_status_for_route(source, record)

    contradicts = any(p.lower() in claim.text.lower() for p in record.contradicts_user_claims)
    supports = any(p.lower() in claim.text.lower() for p in record.supports_user_claims)

    missing: list[str] = []
    if not scope_ok:
        missing.append("scope_mismatch")
    if not juris_ok:
        missing.append("jurisdiction_mismatch")
    if not version_ok:
        missing.append("version_mismatch")
    if not license_ok:
        missing.append("license_blocked")

    if hints.get("expect_outdated") and not version_ok:
        final = "outdated"
    elif contradicts and not hints.get("expect_outdated"):
        final = "contradicted"
    elif supports and scope_ok and license_ok and version_ok:
        final = "supported_within_scope"
    elif hints.get("expect_out_of_scope") and not scope_ok:
        final = "out_of_scope"
    elif not license_ok:
        final = "license_blocked"
    elif match_score < 0.2:
        final = "unsupported"
    elif missing:
        final = "ambiguous"
    else:
        final = "ambiguous"

    strength = match_score
    if supports:
        strength += 0.2
    if contradicts:
        strength += 0.15

    return CitationRoute(
        route_id=new_id("route"),
        claim_id=claim.claim_id,
        source_records=[record.record_id],
        route_type=rtype,  # type: ignore[arg-type]
        route_strength=min(1.0, strength),
        scope_match=scope_ok,
        jurisdiction_match=juris_ok,
        version_match=version_ok,
        license_allowed=license_ok,
        contradiction_present=contradicts,
        missing_dependencies=missing,
        final_status=final,
        notes=f"Matched record {record.record_id} via transparent keyword routing",
    )


def build_routes_for_claim(
    claim: AuthorityClaim,
    ranked_records: list[tuple[float, AuthorityRecord]],
    sources: dict[str, AuthoritySource],
    hints: dict,
) -> list[CitationRoute]:
    routes: list[CitationRoute] = []
    for score, record in ranked_records[:5]:
        source = sources.get(record.source_id)
        if not source:
            continue
        routes.append(build_route(claim, record, source, match_score=score, hints=hints))
    if not routes:
        routes.append(
            CitationRoute(
                route_id=new_id("route"),
                claim_id=claim.claim_id,
                source_records=[],
                route_type="unsupported",
                route_strength=0.0,
                scope_match=False,
                jurisdiction_match=False,
                version_match=False,
                license_allowed=True,
                contradiction_present=False,
                missing_dependencies=["no_matching_records"],
                final_status="unsupported",
                notes="No authority records matched claim keywords",
            )
        )
    return routes