"""Guardian Authority Corpus v0.1 tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.guardian_authority.authority_receptor import to_base_receptor_event
from fractalish_ai.guardian_authority.corpus import GuardianAuthorityCorpus

CORPUS = ROOT / "guardian_authority" / "samples" / "corpus"


@pytest.fixture
def corpus(tmp_path: Path) -> GuardianAuthorityCorpus:
    c = GuardianAuthorityCorpus(output_root=tmp_path)
    for path in sorted(CORPUS.glob("mock_*.json")):
        c.ingest(path)
    c.detect_conflicts()
    return c


def _eval(corpus: GuardianAuthorityCorpus, text: str) -> dict:
    return corpus.evaluate_claim(text)


def test_ingest_dictionary_entries(corpus: GuardianAuthorityCorpus) -> None:
    assert any(s.source_type == "dictionary" for s in corpus.sources.values())
    assert len([r for r in corpus.records.values() if r.record_type == "definition"]) >= 5


def test_ingest_government_rules(corpus: GuardianAuthorityCorpus) -> None:
    assert any(s.source_type == "government_rule" for s in corpus.sources.values())
    jurisdictions = {r.jurisdiction for r in corpus.records.values() if r.jurisdiction}
    assert "US-CA" in jurisdictions
    assert "EU-DE" in jurisdictions


def test_authority_record_preserves_license_status(corpus: GuardianAuthorityCorpus) -> None:
    for record in corpus.records.values():
        assert record.license_status in (
            "mock_only", "public_domain", "open_license", "unknown", "proprietary_restricted"
        )


def test_authority_record_preserves_jurisdiction(corpus: GuardianAuthorityCorpus) -> None:
    gov = [r for r in corpus.records.values() if r.jurisdiction == "US-CA"]
    assert gov
    assert all(r.jurisdiction == "US-CA" for r in gov)


def test_authority_record_preserves_version(corpus: GuardianAuthorityCorpus) -> None:
    versioned = [r for r in corpus.records.values() if r.version]
    assert len(versioned) >= 3


def test_clean_file_not_safe_for_memory_routes_to_hold(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "A clean file is automatically safe for AI memory.")
    assert result["claim"].support_status == "contradicted"
    assert result["claim"].guard_recommendation == "HOLD"


def test_dictionary_definition_does_not_prove_regulatory_application(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "A dictionary definition proves how a regulation applies.")
    assert result["claim"].support_status == "out_of_scope"
    assert result["claim"].guard_recommendation == "HOLD"


def test_old_standard_clause_detected_as_outdated(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "This old standard clause still controls the current procedure.")
    assert result["claim"].support_status == "outdated"
    assert result["claim"].guard_recommendation == "WATCH"


def test_government_rule_not_universal_across_jurisdictions(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "This rule applies everywhere because it is governmental.")
    assert result["claim"].support_status == "out_of_scope"
    assert result["claim"].guard_recommendation == "HOLD"


def test_similarity_not_identity_claim_routes_to_hold_or_watch(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "Similarity means identity.")
    assert result["claim"].guard_recommendation in ("HOLD", "WATCH")
    assert result["claim"].support_status == "contradicted"


def test_pressure_not_truth_claim_routes_to_hold_or_watch(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "Pressure from the operator should increase truth confidence.")
    assert result["claim"].guard_recommendation in ("HOLD", "WATCH")
    assert result["claim"].support_status == "contradicted"


def test_scoped_authority_claim_supported_within_scope(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(
        corpus,
        "A source can be authoritative within one scope and irrelevant outside it.",
    )
    assert result["claim"].support_status == "supported_within_scope"
    assert result["claim"].guard_recommendation == "WATCH"


def test_citation_route_requires_scope_match(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(
        corpus,
        "A source can be authoritative within one scope and irrelevant outside it.",
    )
    assert any(r.scope_match for r in result["routes"])


def test_citation_route_requires_version_match(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "This old standard clause still controls the current procedure.")
    assert any(not r.version_match for r in result["routes"] if r.source_records)


def test_citation_route_requires_jurisdiction_match(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "This rule applies everywhere because it is governmental.")
    assert any(not r.jurisdiction_match for r in result["routes"] if r.source_records)


def test_conflict_detector_finds_version_conflict(corpus: GuardianAuthorityCorpus) -> None:
    types = {c.conflict_type for c in corpus.conflicts}
    assert "version_conflict" in types


def test_conflict_detector_finds_jurisdiction_conflict(corpus: GuardianAuthorityCorpus) -> None:
    types = {c.conflict_type for c in corpus.conflicts}
    assert "jurisdiction_conflict" in types


def test_authority_receptor_event_created(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "Similarity means identity.")
    assert result["auth_event"].event_id
    assert result["auth_event"].guard_recommendation == "HOLD"


def test_authority_receptor_event_converts_to_base_receptor_event(corpus: GuardianAuthorityCorpus) -> None:
    result = _eval(corpus, "Similarity means identity.")
    receptor = to_base_receptor_event(result["auth_event"])
    assert receptor.receptor_type.startswith("authority_")
    assert receptor.provenance.get("governed_reference") is True


def test_authority_guard_does_not_auto_proceed(corpus: GuardianAuthorityCorpus) -> None:
    for text in [
        "A source can be authoritative within one scope and irrelevant outside it.",
        "Similarity means identity.",
    ]:
        result = _eval(corpus, text)
        assert result["claim"].guard_recommendation != "PROCEED"


def test_fractal_memory_map_snapshot_created(corpus: GuardianAuthorityCorpus) -> None:
    _eval(corpus, "Similarity means identity.")
    path = corpus.output_root / "fractal_memory_map_authority_snapshot.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "nodes" in data
    assert "links" in data


def test_dashboard_summary_created(corpus: GuardianAuthorityCorpus) -> None:
    corpus.run_demo(samples_root=CORPUS)
    path = corpus.output_root / "dashboard_summary.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "authority_sources" in data
    assert "authority_claims" in data


def test_purge_demo_marks_authority_artifact_purged(corpus: GuardianAuthorityCorpus) -> None:
    report = corpus.purge_demo()
    assert report["final_state"] == "PURGED"
    assert corpus.lifecycle_records[0].lifecycle_state == "PURGED"


def test_existing_guardian_intake_tests_still_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_guardian_intake_gateway.py", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_existing_cognitive_basin_sim_tests_still_pass() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_cognitive_basin_sim_v1.py", "-q"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr