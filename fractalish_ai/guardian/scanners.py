"""Transparent heuristic scanners — not production security."""

from __future__ import annotations

import re
from typing import Any

PROMPT_INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?previous\s+instructions", "ignore_previous_instructions"),
    (r"disregard\s+system\s+instructions", "disregard_system_instructions"),
    (r"reveal\s+your\s+system\s+prompt", "reveal_system_prompt"),
    (r"leak\s+secrets?", "leak_secrets"),
    (r"exfiltrat", "exfiltration"),
    (r"call\s+this\s+tool\s+without\s+asking", "auto_tool_call"),
    (r"do\s+not\s+tell\s+the\s+user", "hide_from_user"),
    (r"override\s+policy", "override_policy"),
    (r"developer\s+message", "developer_message"),
    (r"hidden\s+instruction", "hidden_instruction"),
    (r"base64\s+decode\s+and\s+execute", "base64_execute"),
    (r"send\s+credentials", "send_credentials"),
]

HIDDEN_INSTRUCTION_PATTERNS = [
    (r"<!--.*?-->", "html_comment_hidden"),
    (r"display\s*:\s*none", "css_hidden"),
    (r"visibility\s*:\s*hidden", "css_invisible"),
    (r"\[hidden\]", "hidden_marker"),
    (r"<!--\s*SYSTEM", "hidden_system_comment"),
]

FALSE_AUTHORITY_PATTERNS = [
    (r"official\s+system\s+policy", "fake_official_policy"),
    (r"treat\s+this\s+as\s+system\s+instruction", "fake_system_instruction"),
    (r"mandatory\s+override", "mandatory_override"),
    (r"legally\s+required\s+to\s+ignore", "fake_legal_override"),
    (r"administrator\s+approved.*no\s+verification", "fake_admin_authority"),
]

LIFECYCLE_SPRAWL_PATTERNS = [
    (r"store\s+this\s+permanently", "permanent_store"),
    (r"add\s+this\s+to\s+memory", "memory_sprawl"),
    (r"cache\s+this\s+everywhere", "cache_sprawl"),
    (r"do\s+not\s+delete\s+this", "no_delete"),
    (r"copy\s+this\s+to\s+all\s+systems", "copy_all_systems"),
]

DLP_PATTERNS = [
    (r"api[_-]?key\s*[:=]", "api_key_pattern"),
    (r"password\s*=", "password_pattern"),
    (r"token\s*=", "token_pattern"),
    (r"secret\s*=", "secret_pattern"),
    (r"sk-[a-zA-Z0-9]{8,}", "openai_key_stub"),
    (r"bearer\s+[a-zA-Z0-9._-]{8,}", "bearer_token"),
    (r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", "private_key"),
]

TOOL_POISONING_PATTERNS = [
    (r"ignore\s+instructions", "tool_ignore_instructions"),
    (r"do\s+not\s+tell", "tool_hide_from_user"),
    (r"send\s+all\s+data\s+to", "tool_exfil_endpoint"),
    (r"automatically\s+call", "tool_auto_call"),
    (r"privileged\s+authority", "tool_fake_authority"),
    (r"without\s+user\s+consent", "tool_no_consent"),
]

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.I)
SHORT_URL = re.compile(r"https?://(bit\.ly|t\.co|goo\.gl|tinyurl)", re.I)


def _match_patterns(text: str, patterns: list[tuple[str, str]]) -> list[str]:
    flags: list[str] = []
    lower = text.lower()
    for pattern, code in patterns:
        if re.search(pattern, lower, re.I | re.DOTALL):
            flags.append(code)
    return flags


def scan_text(content: str) -> dict[str, Any]:
    prompt = _match_patterns(content, PROMPT_INJECTION_PATTERNS)
    hidden = _match_patterns(content, HIDDEN_INSTRUCTION_PATTERNS)
    authority = _match_patterns(content, FALSE_AUTHORITY_PATTERNS)
    sprawl = _match_patterns(content, LIFECYCLE_SPRAWL_PATTERNS)
    dlp = _match_patterns(content, DLP_PATTERNS)

    urls = URL_PATTERN.findall(content)
    link_status = "none"
    if urls:
        link_status = "external_present"
        if any(SHORT_URL.search(u) for u in urls):
            link_status = "suspicious_url"

    suspicious = authority + sprawl
    reason_codes = list(dict.fromkeys(prompt + hidden + dlp + suspicious))

    return {
        "prompt_injection_flags": prompt,
        "hidden_instruction_flags": hidden,
        "tool_poisoning_flags": [],
        "suspicious_patterns": suspicious,
        "dlp_flags": dlp,
        "link_status": link_status,
        "reason_codes": reason_codes,
    }


def scan_mcp_descriptor(data: dict[str, Any]) -> dict[str, Any]:
    text_parts: list[str] = []
    for key in ("name", "description", "instructions", "metadata"):
        val = data.get(key)
        if isinstance(val, str):
            text_parts.append(val)
        elif isinstance(val, dict):
            text_parts.append(str(val))
    resources = data.get("resources") or data.get("tools") or []
    if isinstance(resources, list):
        for item in resources:
            if isinstance(item, dict):
                text_parts.append(str(item.get("description", "")))
                text_parts.append(str(item.get("name", "")))
    combined = "\n".join(text_parts)
    result = scan_text(combined)
    tool_flags = _match_patterns(combined, TOOL_POISONING_PATTERNS)
    result["tool_poisoning_flags"] = list(dict.fromkeys(result.get("tool_poisoning_flags", []) + tool_flags))
    if tool_flags:
        result["reason_codes"] = list(dict.fromkeys(result["reason_codes"] + ["tool_poisoning"]))
    return result