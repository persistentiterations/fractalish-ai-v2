"""Guardian sanitization — bracket suspicious lines, produce model-visible representation."""

from __future__ import annotations

import json
import re
from typing import Any

from fractalish_ai.guardian.models import GuardianSanitizedArtifact, GuardianScanReport
from fractalish_ai.guardian.scanners import (
    FALSE_AUTHORITY_PATTERNS,
    HIDDEN_INSTRUCTION_PATTERNS,
    LIFECYCLE_SPRAWL_PATTERNS,
    PROMPT_INJECTION_PATTERNS,
)

SUSPICIOUS_LINE_PATTERNS = (
    PROMPT_INJECTION_PATTERNS
    + HIDDEN_INSTRUCTION_PATTERNS
    + FALSE_AUTHORITY_PATTERNS
    + LIFECYCLE_SPRAWL_PATTERNS
)


def _line_is_suspicious(line: str) -> str | None:
    for pattern, code in SUSPICIOUS_LINE_PATTERNS:
        if re.search(pattern, line, re.I):
            return code
    return None


def sanitize_text(content: str, intake_id: str, scan: GuardianScanReport) -> GuardianSanitizedArtifact:
    lines = content.splitlines()
    sanitized_lines: list[str] = []
    flagged: list[str] = []
    unsafe_parts: list[str] = []

    for line in lines:
        code = _line_is_suspicious(line)
        if code:
            flagged.append(f"[{code}] {line.strip()}")
            unsafe_parts.append(line.strip())
            sanitized_lines.append(f"[GUARDIAN_FLAGGED:{code}] {line}")
        else:
            sanitized_lines.append(line)

    sanitized_text = "\n".join(sanitized_lines)
    visible_summary = "\n".join(l for l in lines if _line_is_suspicious(l) is None)[:2000]
    unsafe_summary = "; ".join(unsafe_parts[:10]) if unsafe_parts else "none detected"

    allowed = ["sanitized_summary"]
    if scan.risk_level == "LOW" and not scan.prompt_injection_flags:
        allowed.append("metadata_only")

    model_repr = (
        f"[Guardian Sanitized Intake {intake_id}]\n"
        f"Risk: {scan.risk_level} ({scan.risk_score})\n"
        f"Summary: {visible_summary[:500]}\n"
        f"Flagged segments: {len(flagged)}"
    )

    return GuardianSanitizedArtifact(
        intake_id=intake_id,
        sanitized_id=f"san-{intake_id}",
        sanitized_path="",
        sanitized_text=sanitized_text,
        removed_or_flagged_segments=flagged,
        visible_text_summary=visible_summary[:1000],
        unsafe_instruction_summary=unsafe_summary,
        model_visible_representation=model_repr,
        allowed_representations=allowed,
    )


def sanitize_json(data: dict[str, Any], intake_id: str, scan: GuardianScanReport) -> GuardianSanitizedArtifact:
    safe_summary = {
        "intake_id": intake_id,
        "resource_type": data.get("type", "mcp_resource"),
        "name": data.get("name", "unknown"),
        "description_summary": (data.get("description") or "")[:200],
        "tool_count": len(data.get("tools", [])),
        "risk_level": scan.risk_level,
        "flags": scan.reason_codes,
    }
    model_repr = json.dumps(safe_summary, indent=2)
    return GuardianSanitizedArtifact(
        intake_id=intake_id,
        sanitized_id=f"san-{intake_id}",
        sanitized_path="",
        sanitized_text=model_repr,
        removed_or_flagged_segments=scan.tool_poisoning_flags + scan.prompt_injection_flags,
        visible_text_summary=model_repr,
        unsafe_instruction_summary="; ".join(scan.tool_poisoning_flags + scan.prompt_injection_flags) or "none",
        model_visible_representation=model_repr,
        allowed_representations=["metadata_only", "sanitized_summary"],
    )