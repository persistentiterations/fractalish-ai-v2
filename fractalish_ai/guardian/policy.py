"""Guardian risk scoring and decision policy."""

from __future__ import annotations

from fractalish_ai.guardian.models import GuardianDecision, GuardianDecisionState, GuardianScanReport, RiskLevel


def compute_risk_level(score: int) -> RiskLevel:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def score_from_flags(report: GuardianScanReport) -> int:
    score = 0
    score += len(report.prompt_injection_flags) * 18
    score += len(report.hidden_instruction_flags) * 15
    score += len(report.tool_poisoning_flags) * 20
    score += len(report.dlp_flags) * 12
    score += len(report.suspicious_patterns) * 8
    if report.link_status == "external_present":
        score += 5
    if report.link_status == "suspicious_url":
        score += 10

    if report.prompt_injection_flags:
        score = max(score, 55)
    if report.tool_poisoning_flags:
        score = max(score, 60)
    if report.hidden_instruction_flags:
        score = max(score, 45)
    if "exfiltration" in report.prompt_injection_flags:
        score = max(score, 65)
    if any("exfil" in code for code in report.reason_codes):
        score = max(score, 65)

    return min(100, score)


def build_scan_report(intake_id: str, flags: dict) -> GuardianScanReport:
    report = GuardianScanReport(
        intake_id=intake_id,
        scan_status="completed",
        malware_stub_status="stub_clean",
        file_type_status="ok",
        archive_status="not_archive",
        macro_status="not_applicable",
        link_status=flags.get("link_status", "none"),
        prompt_injection_flags=flags.get("prompt_injection_flags", []),
        hidden_instruction_flags=flags.get("hidden_instruction_flags", []),
        tool_poisoning_flags=flags.get("tool_poisoning_flags", []),
        suspicious_patterns=flags.get("suspicious_patterns", []),
        dlp_flags=flags.get("dlp_flags", []),
        reason_codes=flags.get("reason_codes", []),
        raw_model_visible=False,
        sanitized_model_visible=True,
    )
    report.risk_score = score_from_flags(report)
    report.risk_level = compute_risk_level(report.risk_score)
    report.human_review_required = report.risk_level in ("HIGH", "CRITICAL") or bool(
        report.prompt_injection_flags or report.tool_poisoning_flags
    )
    report.safe_to_summarize = report.risk_score < 50
    report.metadata_only = report.risk_level == "CRITICAL" and bool(
        report.prompt_injection_flags or report.tool_poisoning_flags
    )
    if not report.reason_codes:
        report.reason_codes = [f"risk_{report.risk_level.lower()}"]
    return report


def decide(report: GuardianScanReport) -> GuardianDecision:
    level = report.risk_level
    reasons = list(report.reason_codes)

    if level == "CRITICAL":
        decision: GuardianDecisionState = (
            "REVERSE" if report.prompt_injection_flags or report.tool_poisoning_flags else "HOLD"
        )
        blocked = ["raw_content", "hidden_instructions", "tool_metadata"]
        allowed = ["metadata_only"] if report.metadata_only else ["sanitized_summary"]
        review = True
    elif level == "HIGH":
        decision = "HOLD"
        if report.human_review_required and not report.prompt_injection_flags:
            decision = "HUMAN_REVIEW_REQUIRED"
        blocked = ["raw_content"]
        allowed = ["sanitized_summary", "metadata_only"]
        review = True
    elif level == "MEDIUM":
        decision = "WATCH" if report.prompt_injection_flags or report.suspicious_patterns else "SANITIZED_ONLY"
        blocked = ["raw_content"]
        allowed = ["sanitized_summary"]
        review = report.human_review_required
    else:
        decision = "SANITIZED_ONLY"
        blocked = []
        allowed = ["sanitized_summary", "metadata_only"]
        review = False

    return GuardianDecision(
        intake_id=report.intake_id,
        decision=decision,
        reason_codes=reasons,
        blocked_content_types=blocked,
        allowed_representations=allowed,
        requires_operator_review=review,
    ).finalize()