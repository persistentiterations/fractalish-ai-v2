"""RIGOR — reasoning integrity checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

RigorState = Literal["PASS", "HOLD", "REVERSE", "WATCH"]


@dataclass
class RigorFinding:
    analyzer: str
    state: RigorState
    severity: str
    reason: str
    evidence_present: list[str] = field(default_factory=list)
    evidence_missing: list[str] = field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _finding(
    analyzer: str,
    state: RigorState,
    severity: str,
    reason: str,
    *,
    evidence_present: list[str] | None = None,
    evidence_missing: list[str] | None = None,
    recommended_action: str = "",
) -> RigorFinding:
    return RigorFinding(
        analyzer=analyzer,
        state=state,
        severity=severity,
        reason=reason,
        evidence_present=evidence_present or [],
        evidence_missing=evidence_missing or [],
        recommended_action=recommended_action,
    )


def run_rigor_checks(event: dict[str, Any]) -> list[RigorFinding]:
    findings: list[RigorFinding] = []
    source = (event.get("source") or "").strip()
    claim = (event.get("claim") or event.get("content_summary") or "").strip()
    evidence = event.get("evidence") or []
    contradictions = event.get("contradictions") or []
    scope = event.get("scope") or "local"
    risk = event.get("risk_level", "low")
    speculation = bool(event.get("speculation", False))
    similarity_claim = event.get("similarity_claim") or ""
    identity_claim = event.get("identity_claim") or ""

    if not source:
        findings.append(
            _finding(
                "source_presence",
                "HOLD",
                "high" if risk in ("high", "critical") else "medium",
                "No source recorded for incoming claim.",
                evidence_missing=["source_reference"],
                recommended_action="Request or attach source before proceeding.",
            )
        )
    else:
        findings.append(
            _finding(
                "source_presence",
                "PASS",
                "low",
                "Source is present.",
                evidence_present=[source],
            )
        )

    supported = bool(evidence) or event.get("supported", False)
    if claim and not supported:
        findings.append(
            _finding(
                "claim_support",
                "HOLD" if risk in ("high", "critical") else "WATCH",
                "high" if risk in ("high", "critical") else "medium",
                "Claim lacks supporting evidence.",
                evidence_missing=["supporting_evidence"],
                recommended_action="Gather evidence or downgrade claim strength.",
            )
        )
    elif claim:
        findings.append(
            _finding(
                "claim_support",
                "PASS",
                "low",
                "Claim has recorded support.",
                evidence_present=[str(e) for e in evidence[:5]],
            )
        )

    if contradictions:
        evidence_present = []
        for c in contradictions[:5]:
            evidence_present.append(str(c) if not isinstance(c, dict) else f"{c.get('source','?')}: {c.get('claim', c)}")
        findings.append(
            _finding(
                "contradiction",
                "HOLD",
                "high",
                "Unresolved contradiction detected.",
                evidence_present=evidence_present,
                recommended_action="Preserve both claims; resolve before closure.",
            )
        )
    else:
        findings.append(
            _finding(
                "contradiction",
                "PASS",
                "low",
                "No contradiction flagged.",
            )
        )

    if scope in ("universal", "global", "all_domains") and not supported:
        findings.append(
            _finding(
                "scope",
                "HOLD",
                "high",
                "Scope overreach: broad claim without support.",
                evidence_missing=["scoped_evidence"],
                recommended_action="Narrow scope or add domain-specific evidence.",
            )
        )
    else:
        findings.append(
            _finding(
                "scope",
                "PASS",
                "low",
                "Scope within acceptable bounds.",
            )
        )

    if speculation:
        findings.append(
            _finding(
                "speculation",
                "WATCH",
                "medium",
                "Speculative content flagged.",
                recommended_action="Label as hypothesis; avoid presenting as settled fact.",
            )
        )
    else:
        findings.append(
            _finding(
                "speculation",
                "PASS",
                "low",
                "No speculation flag raised.",
            )
        )

    if similarity_claim and identity_claim and similarity_claim == identity_claim:
        findings.append(
            _finding(
                "similarity_vs_identity",
                "HOLD",
                "high",
                "Similarity may be mistaken for identity.",
                evidence_missing=["identity_verification"],
                recommended_action="Compare descriptors; do not equate similarity with sameness.",
            )
        )
    elif similarity_claim and not identity_claim:
        findings.append(
            _finding(
                "similarity_vs_identity",
                "WATCH",
                "medium",
                "Similarity noted without identity verification.",
                recommended_action="Treat as comparison candidate, not identity proof.",
            )
        )
    else:
        findings.append(
            _finding(
                "similarity_vs_identity",
                "PASS",
                "low",
                "No similarity-identity confusion detected.",
            )
        )

    if event.get("boundary_violation"):
        findings.append(
            _finding(
                "boundary",
                "REVERSE",
                "critical",
                "Operator boundary or constraint violated.",
                recommended_action="Stop current action path and revert.",
            )
        )

    overclaim_markers = (
        "proves intelligence",
        "proves agi",
        "solved ai",
        "conscious",
        "sentient",
        "self-aware",
    )
    if claim and any(marker in claim.lower() for marker in overclaim_markers):
        findings.append(
            _finding(
                "overclaim",
                "HOLD",
                "high",
                "Overclaim detected; preserve uncertainty.",
                evidence_missing=["supported_evidence"],
                recommended_action="Downgrade claim; do not assert proof of intelligence.",
            )
        )

    prior_holds = int(event.get("prior_unresolved_hold_count", 0))
    if event.get("assume_prior_settled") and prior_holds > 0 and not supported:
        findings.append(
            _finding(
                "false_continuity",
                "HOLD",
                "high",
                "Attempt to continue as if prior unresolved claim is settled.",
                evidence_missing=["resolution_of_prior_hold"],
                recommended_action="Resolve prior HOLD before claiming closure.",
            )
        )

    return findings