"""Guardian lifecycle and purge management."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fractalish_ai.guardian.models import GuardianIntakeEvent, GuardianLifecycleRecord, LifecycleState, utc_now


def create_lifecycle(intake: GuardianIntakeEvent, *, retention_days: int = 7) -> GuardianLifecycleRecord:
    expires = (datetime.now(timezone.utc) + timedelta(days=retention_days)).isoformat()
    return GuardianLifecycleRecord(
        artifact_id=f"artifact-{uuid.uuid4().hex[:10]}",
        intake_id=intake.intake_id,
        activation_id=intake.activation_id,
        session_id=intake.session_id,
        owner="operator@local",
        privacy_scope="local",
        lifecycle_state="RECEIVED",
        retention_policy=f"local_demo_{retention_days}d",
        expires_at=expires,
        legal_hold=False,
        purge_allowed=True,
        audit_log_reference=f"{intake.intake_id}_audit.jsonl",
    )


def record_derivatives(record: GuardianLifecycleRecord, paths: dict[str, str]) -> None:
    record.derivative_artifacts.update(paths)
    record.derivative_artifacts["quarantine"] = paths.get("quarantine", record.derivative_artifacts.get("quarantine", ""))


def transition(record: GuardianLifecycleRecord, state: LifecycleState, *, reason: str = "") -> None:
    record.lifecycle_state = state
    _ = reason


def purge_outputs(record: GuardianLifecycleRecord, *, keep_audit: bool = True) -> list[str]:
    """Purge generated outputs only — never source samples."""
    deleted: list[str] = []
    record.purge_requested_at = utc_now()
    for key, path_str in list(record.derivative_artifacts.items()):
        if key == "audit" and keep_audit:
            continue
        if not path_str:
            continue
        path = Path(path_str)
        if path.exists() and "samples" not in str(path).replace("\\", "/"):
            if path.is_file():
                path.unlink()
                deleted.append(str(path))
            record.derivative_artifacts[key] = "[PURGED]"
    return deleted