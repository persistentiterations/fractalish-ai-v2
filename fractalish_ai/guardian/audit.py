"""Guardian audit log — JSONL append-only."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from fractalish_ai.guardian.models import GuardianAuditRecord, utc_now


class GuardianAuditLog:
    def __init__(self, audit_dir: Path) -> None:
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.audit_dir / "guardian_audit.jsonl"

    def append(
        self,
        *,
        intake_id: str,
        action: str,
        actor: str,
        before_state: str,
        after_state: str,
        reason: str,
        hash_reference: str = "",
    ) -> GuardianAuditRecord:
        record = GuardianAuditRecord(
            audit_id=f"audit-{uuid.uuid4().hex[:10]}",
            intake_id=intake_id,
            timestamp=utc_now(),
            action=action,
            actor=actor,
            before_state=before_state,
            after_state=after_state,
            reason=reason,
            hash_reference=hash_reference,
        )
        with open(self.log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict()) + "\n")
        per_intake = self.audit_dir / f"{intake_id}_audit.jsonl"
        with open(per_intake, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict()) + "\n")
        return record

    def read_all(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines() if line.strip()]