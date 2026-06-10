"""Guardian Intake Gateway v0.1 tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.guardian.intake import GuardianGateway
from fractalish_ai.receptors import ReceptorType

SAMPLES = ROOT / "guardian" / "samples"
OUTPUT = ROOT / "guardian" / "outputs" / "test_run"


@pytest.fixture
def gateway(tmp_path: Path) -> GuardianGateway:
    return GuardianGateway(output_root=tmp_path)


def test_guardian_scans_benign_file(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "benign_note.txt")
    assert result["scan"].risk_level == "LOW"
    assert result["decision"].decision in ("SANITIZED_ONLY", "PROCEED")
    assert not result["scan"].prompt_injection_flags


def test_prompt_injection_routes_to_hold(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "prompt_injection.txt")
    assert result["scan"].prompt_injection_flags
    assert result["decision"].decision in ("HOLD", "REVERSE", "HUMAN_REVIEW_REQUIRED")
    assert result["lifecycle"].lifecycle_state == "HOLD"


def test_hidden_instruction_flagged(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "hidden_instruction.txt")
    assert result["scan"].hidden_instruction_flags or result["scan"].prompt_injection_flags


def test_fake_authority_not_treated_as_system_instruction(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "fake_authority.txt")
    assert result["scan"].suspicious_patterns
    assert result["scan"].raw_model_visible is False
    assert "sanitized_summary" in result["decision"].allowed_representations


def test_data_exfiltration_trap_routes_to_hold(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "data_exfiltration_trap.txt")
    assert result["scan"].risk_level in ("HIGH", "CRITICAL")
    assert result["decision"].decision in ("HOLD", "REVERSE", "HUMAN_REVIEW_REQUIRED")


def test_email_parsed_into_guardian_event(gateway: GuardianGateway) -> None:
    result = gateway.scan_email(SAMPLES / "email" / "session_upload.eml")
    assert result["intake"].source_channel == "email_mock"
    assert result["receptor"].receptor_type == ReceptorType.GUARDIAN_EMAIL.value


def test_email_prompt_injection_flagged(gateway: GuardianGateway) -> None:
    result = gateway.scan_email(SAMPLES / "email" / "session_upload.eml")
    assert result["scan"].prompt_injection_flags


def test_mcp_clean_resource_scans(gateway: GuardianGateway) -> None:
    result = gateway.scan_mcp(SAMPLES / "mcp" / "clean_resource.json")
    assert result["scan"].risk_level == "LOW"
    assert not result["scan"].tool_poisoning_flags


def test_mcp_poisoned_tool_descriptor_routes_to_hold(gateway: GuardianGateway) -> None:
    result = gateway.scan_mcp(SAMPLES / "mcp" / "poisoned_tool_descriptor.json")
    assert result["scan"].tool_poisoning_flags
    assert result["decision"].decision in ("HOLD", "REVERSE", "HUMAN_REVIEW_REQUIRED")


def test_browser_capture_hidden_prompt_flagged(gateway: GuardianGateway) -> None:
    result = gateway.scan_browser_capture(SAMPLES / "browser" / "page_capture_with_hidden_prompt.txt")
    assert result["scan"].hidden_instruction_flags or result["scan"].prompt_injection_flags


def test_receptor_event_created_from_guardian_scan(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "benign_note.txt")
    receptor = result["receptor"]
    assert receptor.receptor_type == ReceptorType.GUARDIAN_LOCAL_DROP.value
    assert receptor.provenance.get("guardian_intake_id") == result["intake"].intake_id
    assert "basin_summary" in result


def test_raw_content_not_model_visible_by_default(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "prompt_injection.txt")
    assert result["scan"].raw_model_visible is False


def test_sanitized_representation_created(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "prompt_injection.txt")
    sanitized = result["sanitized"]
    assert sanitized.sanitized_text
    assert sanitized.model_visible_representation
    assert Path(sanitized.sanitized_path).exists()


def test_lifecycle_record_created(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "benign_note.txt")
    lifecycle = result["lifecycle"]
    assert lifecycle.artifact_id
    assert lifecycle.lifecycle_state in ("MODEL_VISIBLE", "LIMITED_EXPOSURE", "HOLD", "SANITIZED")


def test_derivative_artifact_map_created(gateway: GuardianGateway) -> None:
    result = gateway.scan_file(SAMPLES / "file_drop" / "benign_note.txt")
    derivatives = result["lifecycle"].derivative_artifacts
    assert "scan_report" in derivatives
    assert "receptor_event" in derivatives
    assert "quarantine" in derivatives


def test_purge_demo_marks_purged(gateway: GuardianGateway) -> None:
    gateway.scan_file(SAMPLES / "file_drop" / "benign_note.txt")
    report = gateway.purge_demo()
    assert report["final_state"] == "PURGED"
    lifecycle_path = gateway.lifecycle_dir / f"{report['intake_id']}_lifecycle.json"
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    assert lifecycle["lifecycle_state"] == "PURGED"


def test_audit_log_records_scan_and_purge(gateway: GuardianGateway) -> None:
    gateway.scan_file(SAMPLES / "file_drop" / "benign_note.txt")
    gateway.purge_demo()
    actions = [r["action"] for r in gateway.audit_log.read_all()]
    assert "RECEIVED" in actions
    assert "SCAN_COMPLETE" in actions
    assert "PURGED" in actions


def test_guardian_outputs_dashboard_summary(gateway: GuardianGateway) -> None:
    gateway.run_demo(samples_root=SAMPLES)
    summary_path = gateway.output_root / "dashboard_summary.json"
    assert summary_path.exists()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert "intakes" in data
    assert len(data["intakes"]) >= 5


def test_existing_receptor_tests_still_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_receptor_event_contract.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_cognitive_basin_sim_still_passes() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_cognitive_basin_sim_v1.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr