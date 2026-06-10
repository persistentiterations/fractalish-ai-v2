"""Jurisdiction matching for authority records."""

from __future__ import annotations

UNIVERSAL = {"global", "universal", "all", "any"}


def normalize_jurisdiction(jurisdiction: str) -> str:
    return jurisdiction.strip().lower().replace("_", "-")


def jurisdiction_match(record_jurisdiction: str, claim_jurisdiction: str = "") -> bool:
    rec = normalize_jurisdiction(record_jurisdiction)
    if not claim_jurisdiction:
        return True
    claim = normalize_jurisdiction(claim_jurisdiction)
    if rec in UNIVERSAL or claim in UNIVERSAL:
        return rec == claim or rec in UNIVERSAL
    if rec == claim:
        return True
    if rec.split("-")[0] == claim.split("-")[0]:
        return True
    return False


def claims_universal_jurisdiction(claim_text: str) -> bool:
    lower = claim_text.lower()
    return "everywhere" in lower or "universal" in lower or "all jurisdictions" in lower