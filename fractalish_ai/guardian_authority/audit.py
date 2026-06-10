"""Authority corpus audit log."""

from __future__ import annotations

import json
from pathlib import Path

from fractalish_ai.guardian_authority.models import new_id, utc_now


class AuthorityAuditLog:
    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, *, action: str, actor: str, target: str, details: dict) -> dict:
        entry = {
            "audit_id": new_id("audit"),
            "timestamp": utc_now(),
            "action": action,
            "actor": actor,
            "target": target,
            "details": details,
        }
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
        return entry

    def read_all(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]