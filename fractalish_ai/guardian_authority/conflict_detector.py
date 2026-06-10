"""Detect conflicts between authority records."""

from __future__ import annotations

from fractalish_ai.guardian_authority.jurisdiction import normalize_jurisdiction
from fractalish_ai.guardian_authority.models import (
    AuthorityConflict,
    AuthorityRecord,
    GuardRecommendation,
    new_id,
)
from fractalish_ai.guardian_authority.versioning import version_conflict_note


def _topic_key(title: str) -> str:
    if ":" in title:
        return title.split(":", 1)[1].strip().lower()
    return title.strip().lower()


def detect_conflicts(records: dict[str, AuthorityRecord]) -> list[AuthorityConflict]:
    conflicts: list[AuthorityConflict] = []
    record_list = list(records.values())

    for i, rec_a in enumerate(record_list):
        for rec_b in record_list[i + 1 :]:
            conflict = _compare_records(rec_a, rec_b)
            if conflict:
                conflicts.append(conflict)
    return conflicts


def _compare_records(rec_a: AuthorityRecord, rec_b: AuthorityRecord) -> AuthorityConflict | None:
    if rec_a.supersedes == rec_b.record_id or rec_b.supersedes == rec_a.record_id:
        return AuthorityConflict(
            conflict_id=new_id("conflict"),
            record_a=rec_a.record_id,
            record_b=rec_b.record_id,
            claim_a=rec_a.claims[0] if rec_a.claims else rec_a.title,
            claim_b=rec_b.claims[0] if rec_b.claims else rec_b.title,
            conflict_type="version_conflict",
            severity="high",
            version_notes=version_conflict_note(rec_a, rec_b),
            guard_recommendation="HOLD",
            notes="Supersession chain detected",
        )

    if rec_a.title == rec_b.title and rec_a.version != rec_b.version:
        return AuthorityConflict(
            conflict_id=new_id("conflict"),
            record_a=rec_a.record_id,
            record_b=rec_b.record_id,
            claim_a=rec_a.claims[0] if rec_a.claims else rec_a.title,
            claim_b=rec_b.claims[0] if rec_b.claims else rec_b.title,
            conflict_type="version_conflict",
            severity="medium",
            version_notes=f"{rec_a.version} vs {rec_b.version}",
            guard_recommendation="WATCH",
            notes="Same title, different versions",
        )

    topic_a = _topic_key(rec_a.title)
    topic_b = _topic_key(rec_b.title)
    if (
        rec_a.record_type in ("rule_excerpt", "regulation_excerpt")
        and rec_b.record_type in ("rule_excerpt", "regulation_excerpt")
        and normalize_jurisdiction(rec_a.jurisdiction) != normalize_jurisdiction(rec_b.jurisdiction)
        and topic_a == topic_b
        and topic_a
    ):
        return AuthorityConflict(
            conflict_id=new_id("conflict"),
            record_a=rec_a.record_id,
            record_b=rec_b.record_id,
            claim_a=rec_a.claims[0] if rec_a.claims else rec_a.title,
            claim_b=rec_b.claims[0] if rec_b.claims else rec_b.title,
            conflict_type="jurisdiction_conflict",
            severity="high",
            jurisdiction_notes=f"{rec_a.jurisdiction} vs {rec_b.jurisdiction}",
            guard_recommendation="HOLD",
            notes="Same rule topic, different jurisdictions",
        )

    if rec_a.scope and rec_b.scope and rec_a.scope != rec_b.scope:
        for ca in rec_a.claims:
            for cb in rec_b.claims:
                if _claims_contradict(ca, cb):
                    return AuthorityConflict(
                        conflict_id=new_id("conflict"),
                        record_a=rec_a.record_id,
                        record_b=rec_b.record_id,
                        claim_a=ca,
                        claim_b=cb,
                        conflict_type="scope_conflict",
                        severity="medium",
                        scope_notes=f"{rec_a.scope} vs {rec_b.scope}",
                        guard_recommendation="HOLD",
                    )

    for ca in rec_a.claims:
        for cb in rec_b.claims:
            if _claims_contradict(ca, cb):
                return AuthorityConflict(
                    conflict_id=new_id("conflict"),
                    record_a=rec_a.record_id,
                    record_b=rec_b.record_id,
                    claim_a=ca,
                    claim_b=cb,
                    conflict_type="direct_contradiction",
                    severity="high",
                    guard_recommendation="HOLD",
                    notes="Direct claim contradiction",
                )

    if rec_a.record_type == "definition" and rec_b.record_type == "definition":
        shared = set(rec_a.definitions.keys()) & set(rec_b.definitions.keys())
        for term in shared:
            if rec_a.definitions[term] != rec_b.definitions[term]:
                return AuthorityConflict(
                    conflict_id=new_id("conflict"),
                    record_a=rec_a.record_id,
                    record_b=rec_b.record_id,
                    claim_a=rec_a.definitions[term],
                    claim_b=rec_b.definitions[term],
                    conflict_type="definition_conflict",
                    severity="medium",
                    guard_recommendation="WATCH",
                    notes=f"Definition conflict for term: {term}",
                )

    if rec_a.license_status == "proprietary_restricted" or rec_b.license_status == "proprietary_restricted":
        if rec_a.title == rec_b.title:
            return AuthorityConflict(
                conflict_id=new_id("conflict"),
                record_a=rec_a.record_id,
                record_b=rec_b.record_id,
                claim_a=rec_a.title,
                claim_b=rec_b.title,
                conflict_type="license_conflict",
                severity="medium",
                guard_recommendation="HOLD",
                notes="License-blocked duplicate reference",
            )
    return None


def _claims_contradict(a: str, b: str) -> bool:
    al, bl = a.lower(), b.lower()
    neg_pairs = [
        ("not", "is"),
        ("never", "always"),
        ("similarity is not identity", "similarity means identity"),
        ("pressure is not truth", "pressure increases truth"),
        ("not permission for memory", "safe for ai memory"),
        ("not universal", "applies everywhere"),
    ]
    for neg, pos in neg_pairs:
        if neg in al and pos in bl:
            return True
        if neg in bl and pos in al:
            return True
    if "not identical" in al and "means identity" in bl:
        return True
    if "not identical" in bl and "means identity" in al:
        return True
    return False