"""Email intake mock — stdlib email parser only."""

from __future__ import annotations

import email
from email import policy
from pathlib import Path
from typing import Any


def parse_eml(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    msg = email.message_from_bytes(raw, policy=policy.default)
    body_text = ""
    attachments: list[dict[str, str]] = []

    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if "attachment" in disp:
                fname = part.get_filename() or "attachment"
                attachments.append({"name": fname, "type": ctype, "size": str(len(part.get_payload(decode=True) or b""))})
            elif ctype == "text/plain" and not body_text:
                body_text = part.get_content() or ""
    else:
        body_text = msg.get_content() or ""

    return {
        "subject": msg.get("Subject", ""),
        "from": msg.get("From", ""),
        "to": msg.get("To", ""),
        "date": msg.get("Date", ""),
        "body": body_text,
        "attachments": attachments,
        "headers": {k: msg[k] for k in ("Subject", "From", "To", "Date") if msg[k]},
    }


def email_to_scan_text(parsed: dict[str, Any]) -> str:
    parts = [
        f"Subject: {parsed.get('subject', '')}",
        f"From: {parsed.get('from', '')}",
        f"Date: {parsed.get('date', '')}",
        "",
        parsed.get("body", ""),
    ]
    for att in parsed.get("attachments", []):
        parts.append(f"Attachment: {att.get('name')} ({att.get('type')})")
    return "\n".join(parts)