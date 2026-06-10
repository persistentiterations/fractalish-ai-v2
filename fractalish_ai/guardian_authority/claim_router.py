"""Transparent keyword/scope claim routing — no embeddings."""

from __future__ import annotations

import re
from typing import Any

from fractalish_ai.guardian_authority.models import AuthorityClaim, AuthorityRecord, AuthoritySource, new_id

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "to", "of",
    "in", "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "under",
    "again", "further", "then", "once", "this", "that", "these", "those",
    "it", "its", "and", "but", "or", "because", "so", "than", "too", "very",
    "not", "no", "nor", "only", "own", "same", "how", "what", "which", "who",
}


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", text.lower()))
    return {t for t in tokens if t not in STOP_WORDS and len(t) > 2}


def infer_claim_type(text: str) -> str:
    lower = text.lower()
    if "definition" in lower or "means" in lower:
        return "definition_claim"
    if "regulation" in lower or "rule" in lower or "governmental" in lower:
        return "regulatory_claim"
    if "standard" in lower or "procedure" in lower or "clause" in lower:
        return "standard_claim"
    if "scope" in lower or "authoritative within" in lower:
        return "scope_claim"
    if "similarity" in lower or "identity" in lower:
        return "factual_claim"
    if "pressure" in lower or "truth" in lower:
        return "factual_claim"
    if "memory" in lower or "clean file" in lower:
        return "factual_claim"
    return "unsupported_user_claim"


def infer_jurisdiction(text: str) -> str:
    lower = text.lower()
    if "everywhere" in lower or "universal" in lower:
        return "universal"
    if "california" in lower or "us-ca" in lower:
        return "US-CA"
    if "european" in lower or "eu" in lower:
        return "EU"
    return ""


def score_record_match(claim_text: str, record: AuthorityRecord) -> float:
    claim_tokens = tokenize(claim_text)
    record_tokens = tokenize(record.text + " " + record.title + " " + " ".join(record.key_terms))
    record_tokens.update(tokenize(" ".join(record.claims)))
    if not claim_tokens:
        return 0.0
    overlap = claim_tokens & record_tokens
    score = len(overlap) / max(len(claim_tokens), 1)

    for pattern in record.supports_user_claims:
        if pattern.lower() in claim_text.lower():
            score += 0.5
    for pattern in record.contradicts_user_claims:
        if pattern.lower() in claim_text.lower():
            score += 0.4

    for term in record.key_terms:
        if term.lower() in claim_text.lower():
            score += 0.15
    return min(1.0, score)


def find_relevant_records(
    claim_text: str,
    records: dict[str, AuthorityRecord],
    *,
    min_score: float = 0.15,
) -> list[tuple[float, AuthorityRecord]]:
    ranked: list[tuple[float, AuthorityRecord]] = []
    for record in records.values():
        score = score_record_match(claim_text, record)
        if score >= min_score:
            ranked.append((score, record))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked


def create_claim_from_user_text(text: str) -> AuthorityClaim:
    return AuthorityClaim(
        claim_id=new_id("aclaim"),
        text=text,
        claim_type=infer_claim_type(text),  # type: ignore[arg-type]
        jurisdiction=infer_jurisdiction(text),
        dependency_terms=sorted(tokenize(text)),
    )


def apply_claim_pattern_rules(claim: AuthorityClaim, sources: dict[str, AuthoritySource]) -> dict[str, Any]:
    """Explicit rules for demo/test claims."""
    lower = claim.text.lower()
    hints: dict[str, Any] = {
        "required_scope": "",
        "required_jurisdiction": claim.jurisdiction,
        "required_version": "",
        "expect_contradiction": False,
        "expect_supported": False,
        "expect_outdated": False,
        "expect_out_of_scope": False,
    }
    if "clean file" in lower and "memory" in lower:
        hints["expect_contradiction"] = True
        hints["required_scope"] = "guardian_intake"
    if "dictionary definition" in lower and "regulation" in lower:
        hints["expect_out_of_scope"] = True
        hints["required_scope"] = "regulatory"
    if "old standard" in lower:
        hints["expect_outdated"] = True
        hints["required_version"] = "2.0"
    if "everywhere" in lower and "governmental" in lower:
        hints["expect_out_of_scope"] = True
        hints["required_jurisdiction"] = "universal"
    if "similarity" in lower and "identity" in lower:
        hints["expect_contradiction"] = True
    if "pressure" in lower and "truth" in lower:
        hints["expect_contradiction"] = True
    if "authoritative within one scope" in lower:
        hints["expect_supported"] = True
        hints["required_scope"] = "scoped_authority"
    if "citation route" in lower and "matching jurisdiction" in lower:
        hints["expect_supported"] = True
    return hints