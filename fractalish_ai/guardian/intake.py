"""Guardian Intake Gateway orchestrator."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import uuid
from pathlib import Path
from typing import Any

from fractalish_ai.basin_link import receptor_event_to_decision_record
from fractalish_ai.guardian.audit import GuardianAuditLog
from fractalish_ai.guardian.email_receptor import email_to_scan_text, parse_eml
from fractalish_ai.guardian.lifecycle import create_lifecycle, purge_outputs, record_derivatives, transition
from fractalish_ai.guardian.mcp_guard import load_mcp_resource, scan_mcp_file
from fractalish_ai.guardian.models import (
    GuardianDecision,
    GuardianIntakeEvent,
    GuardianLifecycleRecord,
    GuardianSanitizedArtifact,
    GuardianScanReport,
    new_intake_id,
    utc_now,
)
from fractalish_ai.guardian.policy import build_scan_report, decide
from fractalish_ai.guardian.receptor_bridge import bridge_to_receptor
from fractalish_ai.guardian.sanitizer import sanitize_json, sanitize_text
from fractalish_ai.guardian.scanners import scan_text
from fractalish_ai.receptors import ReceptorType


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class GuardianGateway:
    """Local-first zero-trust intake membrane."""

    def __init__(self, output_root: Path | None = None) -> None:
        if output_root is None:
            output_root = Path(__file__).resolve().parents[2] / "guardian" / "outputs"
        self.output_root = Path(output_root)
        self.quarantine_dir = self.output_root / "quarantine"
        self.sanitized_dir = self.output_root / "sanitized"
        self.reports_dir = self.output_root / "reports"
        self.audit_dir = self.output_root / "audit"
        self.receptor_dir = self.output_root / "receptor_events"
        self.lifecycle_dir = self.output_root / "lifecycle"
        self.audit_log = GuardianAuditLog(self.audit_dir)
        self.activation_id = f"act-{uuid.uuid4().hex[:12]}"
        self.session_id = f"sess-{uuid.uuid4().hex[:12]}"

    def _quarantine(self, source: Path, intake_id: str) -> Path:
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        dest = self.quarantine_dir / f"{intake_id}_{source.name}"
        shutil.copy2(source, dest)
        return dest

    def _build_sanitized(
        self,
        intake: GuardianIntakeEvent,
        raw_text: str,
        scan: GuardianScanReport,
        decision: GuardianDecision,
        *,
        is_json: bool = False,
        json_data: dict[str, Any] | None = None,
    ) -> GuardianSanitizedArtifact:
        if is_json and json_data is not None:
            sanitized = sanitize_json(json_data, intake.intake_id, scan)
        else:
            sanitized = sanitize_text(raw_text, intake.intake_id, scan)
        sanitized.allowed_representations = decision.allowed_representations

        sanitized_path = self.sanitized_dir / f"{sanitized.sanitized_id}.txt"
        sanitized_path.parent.mkdir(parents=True, exist_ok=True)
        sanitized_path.write_text(sanitized.sanitized_text, encoding="utf-8")
        sanitized.sanitized_path = str(sanitized_path)
        return sanitized

    def _write_outputs(
        self,
        intake: GuardianIntakeEvent,
        scan: GuardianScanReport,
        sanitized: GuardianSanitizedArtifact,
        lifecycle: GuardianLifecycleRecord,
        decision: GuardianDecision,
        receptor_dict: dict[str, Any],
        quarantine_path: Path,
        basin_summary: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        paths: dict[str, str] = {
            "quarantine": str(quarantine_path),
            "intake": str(self.reports_dir / f"{intake.intake_id}_intake.json"),
            "scan_report": str(self.reports_dir / f"{intake.intake_id}_scan.json"),
            "sanitized": str(self.sanitized_dir / f"{intake.intake_id}_sanitized.json"),
            "sanitized_text": sanitized.sanitized_path,
            "decision": str(self.reports_dir / f"{intake.intake_id}_decision.json"),
            "lifecycle": str(self.lifecycle_dir / f"{intake.intake_id}_lifecycle.json"),
            "receptor_event": str(self.receptor_dir / f"{intake.intake_id}_receptor.json"),
            "audit": str(self.audit_dir / f"{intake.intake_id}_audit.jsonl"),
        }
        if basin_summary:
            paths["basin_summary"] = str(self.reports_dir / f"{intake.intake_id}_basin.json")

        _write_json(Path(paths["intake"]), intake.to_dict())
        _write_json(Path(paths["scan_report"]), scan.to_dict())
        _write_json(Path(paths["sanitized"]), sanitized.to_dict())
        _write_json(Path(paths["decision"]), decision.to_dict())
        _write_json(Path(paths["receptor_event"]), receptor_dict)
        if basin_summary:
            _write_json(Path(paths["basin_summary"]), basin_summary)

        record_derivatives(lifecycle, paths)
        _write_json(Path(paths["lifecycle"]), lifecycle.to_dict())
        return paths

    def process_intake(
        self,
        source_path: Path,
        *,
        source_channel: str,
        receptor_type: ReceptorType | None = None,
        source_identity: str = "local_operator",
        raw_text: str | None = None,
        flags: dict[str, Any] | None = None,
        is_json: bool = False,
        json_data: dict[str, Any] | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        source_path = Path(source_path).resolve()
        intake_id = new_intake_id()
        quarantine_path = self._quarantine(source_path, intake_id)
        detected_mime, _ = mimetypes.guess_type(str(source_path))

        intake = GuardianIntakeEvent(
            intake_id=intake_id,
            activation_id=self.activation_id,
            session_id=self.session_id,
            source_channel=source_channel,
            source_identity=source_identity,
            received_at=utc_now(),
            raw_path=str(source_path),
            declared_mime_type=detected_mime or "application/octet-stream",
            detected_mime_type=detected_mime or "application/octet-stream",
            file_name=source_path.name,
            size_bytes=source_path.stat().st_size,
            sha256=_sha256(source_path),
            raw_available=True,
            quarantine_path=str(quarantine_path),
            notes=notes,
        )

        self.audit_log.append(
            intake_id=intake_id,
            action="RECEIVED",
            actor="guardian_gateway",
            before_state="",
            after_state="RECEIVED",
            reason="intake_received",
            hash_reference=intake.sha256,
        )

        lifecycle = create_lifecycle(intake)
        transition(lifecycle, "QUARANTINED", reason="copied_to_quarantine")
        self.audit_log.append(
            intake_id=intake_id,
            action="QUARANTINE",
            actor="guardian_gateway",
            before_state="RECEIVED",
            after_state="QUARANTINED",
            reason="quarantine_copy",
            hash_reference=intake.sha256,
        )

        transition(lifecycle, "SCANNING", reason="scan_started")
        if raw_text is None:
            raw_text = source_path.read_text(encoding="utf-8", errors="replace")
        if flags is None:
            flags = scan_text(raw_text)

        scan = build_scan_report(intake_id, flags)
        decision = decide(scan)
        sanitized = self._build_sanitized(
            intake, raw_text, scan, decision, is_json=is_json, json_data=json_data
        )

        if decision.decision in ("HOLD", "REVERSE", "HUMAN_REVIEW_REQUIRED"):
            transition(lifecycle, "HOLD", reason=decision.decision)
        elif decision.decision == "WATCH":
            transition(lifecycle, "LIMITED_EXPOSURE", reason="watch_policy")
        else:
            transition(lifecycle, "SANITIZED", reason="sanitization_complete")
            transition(lifecycle, "MODEL_VISIBLE", reason="sanitized_representation_ready")

        receptor = bridge_to_receptor(intake, scan, sanitized, lifecycle, decision, receptor_type)
        receptor_dict = receptor.to_dict()
        basin_record = receptor_event_to_decision_record(receptor)
        basin_summary = {
            "intake_id": intake_id,
            "guard_decision": basin_record.get("guard_decision", {}),
            "risk_level": scan.risk_level,
            "lifecycle_state": lifecycle.lifecycle_state,
            "allowed_representations": decision.allowed_representations,
            "receptor_event_id": receptor.event_id,
        }

        paths = self._write_outputs(
            intake, scan, sanitized, lifecycle, decision, receptor_dict, quarantine_path, basin_summary
        )

        self.audit_log.append(
            intake_id=intake_id,
            action="SCAN_COMPLETE",
            actor="guardian_gateway",
            before_state="SCANNING",
            after_state=lifecycle.lifecycle_state,
            reason=f"risk_{scan.risk_level}_{decision.decision}",
            hash_reference=decision.decision_hash,
        )

        return {
            "intake": intake,
            "scan": scan,
            "sanitized": sanitized,
            "lifecycle": lifecycle,
            "decision": decision,
            "receptor": receptor,
            "paths": paths,
            "basin_summary": basin_summary,
        }

    def scan_file(self, path: Path, channel: str = "local_file_drop") -> dict[str, Any]:
        return self.process_intake(
            path,
            source_channel=channel,
            receptor_type=ReceptorType.GUARDIAN_LOCAL_DROP,
            source_identity="file_drop",
        )

    def scan_email(self, eml_path: Path) -> dict[str, Any]:
        parsed = parse_eml(eml_path)
        scan_body = email_to_scan_text(parsed)
        flags = scan_text(scan_body)
        return self.process_intake(
            eml_path,
            source_channel="email_mock",
            receptor_type=ReceptorType.GUARDIAN_EMAIL,
            source_identity=parsed.get("from", "unknown_sender"),
            raw_text=scan_body,
            flags=flags,
            notes=f"subject={parsed.get('subject', '')}; attachments={len(parsed.get('attachments', []))}",
        )

    def scan_mcp(self, json_path: Path) -> dict[str, Any]:
        data = load_mcp_resource(json_path)
        flags = scan_mcp_file(json_path)
        raw_text = json.dumps(data, indent=2)
        return self.process_intake(
            json_path,
            source_channel="mcp_resource",
            receptor_type=ReceptorType.GUARDIAN_MCP_RESOURCE,
            source_identity="mcp_descriptor",
            raw_text=raw_text,
            flags=flags,
            is_json=True,
            json_data=data,
        )

    def scan_browser_capture(self, path: Path) -> dict[str, Any]:
        return self.process_intake(
            path,
            source_channel="browser_capture_mock",
            receptor_type=ReceptorType.GUARDIAN_BROWSER_CAPTURE,
            source_identity="browser_capture",
        )

    def run_demo(self, samples_root: Path | None = None) -> list[dict[str, Any]]:
        if samples_root is None:
            samples_root = Path(__file__).resolve().parents[2] / "guardian" / "samples"
        results: list[dict[str, Any]] = []

        file_drop = samples_root / "file_drop"
        for name in sorted(file_drop.glob("*.txt")):
            results.append(self.scan_file(name))

        email_sample = samples_root / "email" / "session_upload.eml"
        if email_sample.exists():
            results.append(self.scan_email(email_sample))

        for name in sorted((samples_root / "mcp").glob("*.json")):
            results.append(self.scan_mcp(name))

        browser = samples_root / "browser" / "page_capture_with_hidden_prompt.txt"
        if browser.exists():
            results.append(self.scan_browser_capture(browser))

        self.write_dashboard_summary(results)
        return results

    def write_dashboard_summary(self, results: list[dict[str, Any]]) -> Path:
        summary_path = self.output_root / "dashboard_summary.json"
        entries = []
        for result in results:
            intake = result["intake"]
            scan = result["scan"]
            decision = result["decision"]
            lifecycle = result["lifecycle"]
            entries.append(
                {
                    "intake_id": intake.intake_id,
                    "source_channel": intake.source_channel,
                    "file_name": intake.file_name,
                    "risk_score": scan.risk_score,
                    "risk_level": scan.risk_level,
                    "decision": decision.decision,
                    "lifecycle_state": lifecycle.lifecycle_state,
                    "prompt_injection_flags": scan.prompt_injection_flags,
                    "tool_poisoning_flags": scan.tool_poisoning_flags,
                    "hidden_instruction_flags": scan.hidden_instruction_flags,
                    "dlp_flags": scan.dlp_flags,
                    "raw_model_visible": scan.raw_model_visible,
                    "sanitized_model_visible": scan.sanitized_model_visible,
                    "derivative_artifacts": lifecycle.derivative_artifacts,
                    "purge_status": lifecycle.lifecycle_state,
                    "received_at": intake.received_at,
                }
            )
        payload = {"intakes": entries, "audit_timeline": self.audit_log.read_all()}
        _write_json(summary_path, payload)
        return summary_path

    def purge_demo(self, intake_id: str | None = None) -> dict[str, Any]:
        lifecycle_files = sorted(self.lifecycle_dir.glob("*_lifecycle.json"))
        if not lifecycle_files:
            raise RuntimeError("No lifecycle records found. Run scan or run-demo first.")

        if intake_id is None:
            intake_id = json.loads(lifecycle_files[0].read_text(encoding="utf-8"))["intake_id"]

        lifecycle_path = self.lifecycle_dir / f"{intake_id}_lifecycle.json"
        if not lifecycle_path.exists():
            raise FileNotFoundError(f"No lifecycle for intake {intake_id}")

        lifecycle = GuardianLifecycleRecord(**json.loads(lifecycle_path.read_text(encoding="utf-8")))
        prior_state = lifecycle.lifecycle_state
        transition(lifecycle, "PURGE_PENDING", reason="operator_purge_demo")
        self.audit_log.append(
            intake_id=intake_id,
            action="PURGE_REQUESTED",
            actor="cli_purge_demo",
            before_state=prior_state,
            after_state="PURGE_PENDING",
            reason="purge_demo",
            hash_reference=lifecycle.artifact_id,
        )

        deleted = purge_outputs(lifecycle)
        transition(lifecycle, "PURGED", reason="purge_completed")
        lifecycle.purge_completed_at = utc_now()
        lifecycle.purge_allowed = False

        purge_report = {
            "intake_id": intake_id,
            "deleted_files": deleted,
            "final_state": "PURGED",
            "purge_completed_at": lifecycle.purge_completed_at,
        }
        _write_json(self.reports_dir / f"{intake_id}_purge_report.json", purge_report)
        _write_json(lifecycle_path, lifecycle.to_dict())

        self.audit_log.append(
            intake_id=intake_id,
            action="PURGED",
            actor="cli_purge_demo",
            before_state="PURGE_PENDING",
            after_state="PURGED",
            reason="derivative_outputs_removed",
            hash_reference=intake_id,
        )

        self._rebuild_dashboard_summary()
        return purge_report

    def _rebuild_dashboard_summary(self) -> Path:
        results: list[dict[str, Any]] = []
        for lf in sorted(self.lifecycle_dir.glob("*_lifecycle.json")):
            intake_id = lf.stem.replace("_lifecycle", "")
            ip = self.reports_dir / f"{intake_id}_intake.json"
            sp = self.reports_dir / f"{intake_id}_scan.json"
            dp = self.reports_dir / f"{intake_id}_decision.json"
            if not all(p.exists() for p in (ip, sp, dp)):
                continue
            results.append(
                {
                    "intake": GuardianIntakeEvent(**json.loads(ip.read_text(encoding="utf-8"))),
                    "scan": GuardianScanReport(**json.loads(sp.read_text(encoding="utf-8"))),
                    "decision": GuardianDecision(**json.loads(dp.read_text(encoding="utf-8"))),
                    "lifecycle": GuardianLifecycleRecord(**json.loads(lf.read_text(encoding="utf-8"))),
                }
            )
        return self.write_dashboard_summary(results)


def process_file_intake(path: Path, output_root: Path | None = None) -> dict[str, Any]:
    """Convenience entry for file drop intake."""
    return GuardianGateway(output_root).scan_file(path)