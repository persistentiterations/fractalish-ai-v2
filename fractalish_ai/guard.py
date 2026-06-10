"""GUARD — ternary activation gate: PROCEED / HOLD / REVERSE / WATCH."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

GuardDecision = Literal["PROCEED", "HOLD", "REVERSE", "WATCH"]


@dataclass
class GuardResult:
    decision: GuardDecision
    reason: str
    triggered_by: list[str]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_guard(rigor_findings: list[dict[str, Any]], event: dict[str, Any] | None = None) -> GuardResult:
    event = event or {}
    triggered: list[str] = []

    for finding in rigor_findings:
        if finding["state"] == "REVERSE":
            triggered.append(finding["analyzer"])
            return GuardResult(
                decision="REVERSE",
                reason=finding["reason"],
                triggered_by=triggered,
                confidence=0.9,
            )

    hold_findings = [f for f in rigor_findings if f["state"] == "HOLD"]
    if hold_findings:
        high_risk = event.get("risk_level") in ("high", "critical")
        unsupported = any(f["analyzer"] == "claim_support" for f in hold_findings)
        contradiction = any(f["analyzer"] == "contradiction" for f in hold_findings)
        triggered = [f["analyzer"] for f in hold_findings]
        if high_risk and unsupported:
            return GuardResult(
                decision="HOLD",
                reason="Unsupported high-risk claim requires evidence before proceeding.",
                triggered_by=triggered,
                confidence=0.85,
            )
        if contradiction:
            return GuardResult(
                decision="HOLD",
                reason="Contradiction without resolution; preserve uncertainty.",
                triggered_by=triggered,
                confidence=0.88,
            )
        return GuardResult(
            decision="HOLD",
            reason=hold_findings[0]["reason"],
            triggered_by=triggered,
            confidence=0.75,
        )

    watch_findings = [f for f in rigor_findings if f["state"] == "WATCH"]
    if watch_findings:
        triggered = [f["analyzer"] for f in watch_findings]
        return GuardResult(
            decision="WATCH",
            reason="Mild uncertainty; continue with caution.",
            triggered_by=triggered,
            confidence=0.6,
        )

    return GuardResult(
        decision="PROCEED",
        reason="Supported low-risk continuation.",
        triggered_by=[],
        confidence=0.7,
    )