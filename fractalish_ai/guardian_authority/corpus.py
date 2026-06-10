"""Guardian Authority Corpus orchestrator."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fractalish_ai.basin_link import receptor_event_to_decision_record
from fractalish_ai.fractal_memory_map import FractalMemoryMap, FractalMemoryLink, FractalMemoryNode
from fractalish_ai.guardian_authority.audit import AuthorityAuditLog
from fractalish_ai.guardian_authority.authority_receptor import (
    build_authority_receptor_event,
    to_base_receptor_event,
)
from fractalish_ai.guardian_authority.citation_routes import build_routes_for_claim
from fractalish_ai.guardian_authority.claim_router import (
    apply_claim_pattern_rules,
    create_claim_from_user_text,
    find_relevant_records,
)
from fractalish_ai.guardian_authority.conflict_detector import detect_conflicts
from fractalish_ai.guardian_authority.dashboard_export import export_dashboard_summary
from fractalish_ai.guardian_authority.ingestion import ingest_file
from fractalish_ai.guardian_authority.models import (
    AuthorityClaim,
    AuthorityConflict,
    AuthorityLifecycleRecord,
    AuthorityRecord,
    AuthoritySource,
    CitationRoute,
    new_id,
    utc_now,
)
from fractalish_ai.guardian_authority.reasoning import evaluate_claim


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class GuardianAuthorityCorpus:
    """Local-first governed authority reference layer."""

    def __init__(self, output_root: Path | None = None) -> None:
        if output_root is None:
            output_root = Path(__file__).resolve().parents[2] / "guardian_authority" / "outputs"
        self.output_root = Path(output_root)
        self.receptor_dir = self.output_root / "receptor_events"
        self.sources: dict[str, AuthoritySource] = {}
        self.records: dict[str, AuthorityRecord] = {}
        self.claims: dict[str, AuthorityClaim] = {}
        self.routes: list[CitationRoute] = []
        self.conflicts: list[AuthorityConflict] = []
        self.lifecycle_records: list[AuthorityLifecycleRecord] = []
        self.guard_decisions: list[dict[str, Any]] = []
        self.activation_id = f"act-{uuid.uuid4().hex[:12]}"
        self.session_id = f"sess-{uuid.uuid4().hex[:12]}"
        self.audit = AuthorityAuditLog(self.output_root / "audit.jsonl")

    def _persist_corpus(self) -> None:
        _write_json(self.output_root / "authority_sources.json", [s.to_dict() for s in self.sources.values()])
        _write_json(self.output_root / "authority_records.json", [r.to_dict() for r in self.records.values()])
        _write_json(self.output_root / "authority_claims.json", [c.to_dict() for c in self.claims.values()])
        _write_json(self.output_root / "citation_routes.json", [r.to_dict() for r in self.routes])
        _write_json(self.output_root / "conflicts.json", [c.to_dict() for c in self.conflicts])
        _write_json(
            self.output_root / "lifecycle_records.json",
            [lr.to_dict() for lr in self.lifecycle_records],
        )

    def ingest(self, path: Path) -> dict[str, Any]:
        path = Path(path).resolve()
        source, records = ingest_file(path)
        self.sources[source.source_id] = source
        ingested_ids: list[str] = []
        for record in records:
            self.records[record.record_id] = record
            ingested_ids.append(record.record_id)

        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        lifecycle = AuthorityLifecycleRecord(
            artifact_id=new_id("artifact"),
            source_id=source.source_id,
            record_ids=ingested_ids,
            lifecycle_state="INGESTED",
            retention_policy="local_demo_30d",
            expires_at=expires,
            purge_allowed=True,
            derivative_artifacts={"corpus_file": str(path)},
            audit_log_reference=str(self.output_root / "audit.jsonl"),
        )
        lifecycle.lifecycle_state = "INDEXED"
        self.lifecycle_records.append(lifecycle)

        self.audit.append(
            action="INGEST",
            actor="authority_corpus",
            target=source.source_id,
            details={"file": str(path), "records": len(records), "license": source.license_status},
        )
        self._persist_corpus()
        return {"source": source, "records": records, "lifecycle": lifecycle}

    def detect_conflicts(self) -> list[AuthorityConflict]:
        self.conflicts = detect_conflicts(self.records)
        _write_json(self.output_root / "conflicts.json", [c.to_dict() for c in self.conflicts])
        self.audit.append(
            action="DETECT_CONFLICTS",
            actor="authority_corpus",
            target="corpus",
            details={"conflict_count": len(self.conflicts)},
        )
        return self.conflicts

    def evaluate_claim(self, claim_text: str) -> dict[str, Any]:
        claim = create_claim_from_user_text(claim_text)
        hints = apply_claim_pattern_rules(claim, self.sources)
        ranked = find_relevant_records(claim_text, self.records)
        routes = build_routes_for_claim(claim, ranked, self.sources, hints)
        if not self.conflicts:
            self.detect_conflicts()
        claim = evaluate_claim(claim, routes, self.conflicts, hints)
        self.claims[claim.claim_id] = claim
        self.routes.extend(routes)

        primary_record = self.records.get(routes[0].source_records[0]) if routes and routes[0].source_records else None
        primary_source = (
            self.sources.get(primary_record.source_id)
            if primary_record
            else next(iter(self.sources.values()), None)
        )
        if not primary_source:
            primary_source = AuthoritySource(
                source_id="src-fallback",
                source_name="fallback",
                source_type="mock_reference",
                publisher="local",
                authority_level="mock",
                jurisdiction="local",
                domain="general",
                license_status="mock_only",
            )

        event_id = new_id("aevt")
        auth_event = build_authority_receptor_event(
            event_id=event_id,
            activation_id=self.activation_id,
            session_id=self.session_id,
            source=primary_source,
            record=primary_record,
            claim=claim,
            routes=routes,
            conflicts=self.conflicts,
        )
        receptor = to_base_receptor_event(auth_event)
        basin_record = receptor_event_to_decision_record(receptor)

        guard_entry = {
            "claim_id": claim.claim_id,
            "claim_text": claim.text,
            "support_status": claim.support_status,
            "authority_guard_recommendation": claim.guard_recommendation,
            "basin_guard_decision": basin_record.get("guard_decision", {}),
            "receptor_event_id": event_id,
        }
        self.guard_decisions.append(guard_entry)
        _write_json(self.output_root / "guard_decisions.json", self.guard_decisions)

        receptor_path = self.receptor_dir / f"{event_id}_receptor.json"
        _write_json(receptor_path, receptor.to_dict())
        _write_json(self.receptor_dir / f"{event_id}_authority.json", auth_event.to_dict())

        fmm_snapshot = self._build_fmm_snapshot(claim, routes, primary_source, primary_record)
        _write_json(self.output_root / "fractal_memory_map_authority_snapshot.json", fmm_snapshot)

        session_update = {
            "activation_id": self.activation_id,
            "session_id": self.session_id,
            "authority_evaluations": len(self.claims),
            "unresolved_holds": [
                c.claim_id for c in self.claims.values() if c.guard_recommendation in ("HOLD", "REVERSE")
            ],
            "last_claim": claim.to_dict(),
            "timestamp": utc_now(),
        }
        _write_json(self.output_root / "session_glyph_authority_update.json", session_update)

        self.audit.append(
            action="EVALUATE_CLAIM",
            actor="authority_corpus",
            target=claim.claim_id,
            details={
                "support_status": claim.support_status,
                "guard": claim.guard_recommendation,
                "routes": len(routes),
            },
        )
        self._persist_corpus()
        return {
            "claim": claim,
            "routes": routes,
            "auth_event": auth_event,
            "receptor": receptor,
            "basin_record": basin_record,
            "guard_entry": guard_entry,
        }

    def _build_fmm_snapshot(
        self,
        claim: AuthorityClaim,
        routes: list[CitationRoute],
        source: AuthoritySource | None,
        record: AuthorityRecord | None,
    ) -> dict[str, Any]:
        fmm = FractalMemoryMap(center_node_id="authority_hub")
        fmm.add_node(
            FractalMemoryNode(
                node_id="authority_hub",
                label="Authority Corpus Hub",
                salience=0.9,
                domain_tags=["authority"],
                source="guardian_authority",
            )
        )
        if source:
            sid = f"src_{source.source_id}"
            fmm.add_node(
                FractalMemoryNode(
                    node_id=sid,
                    label=source.source_name,
                    salience=0.7,
                    domain_tags=[source.source_type, source.jurisdiction],
                    source=source.publisher,
                )
            )
            fmm.add_link(
                FractalMemoryLink("authority_hub", sid, "semantic", strength=0.8, notes="authority source")
            )
        if record:
            rid = f"rec_{record.record_id}"
            fmm.add_node(
                FractalMemoryNode(
                    node_id=rid,
                    label=record.title,
                    salience=0.65,
                    uncertainty_score=record.uncertainty,
                    domain_tags=[record.record_type, record.scope],
                    source=record.source_id,
                )
            )
            if source:
                fmm.add_link(
                    FractalMemoryLink(f"src_{source.source_id}", rid, "semantic", strength=0.75)
                )
        cid = f"claim_{claim.claim_id}"
        hold = claim.guard_recommendation in ("HOLD", "REVERSE") or claim.support_status in (
            "contradicted", "unsupported", "out_of_scope", "hold"
        )
        fmm.add_node(
            FractalMemoryNode(
                node_id=cid,
                label=claim.text[:80],
                salience=0.6,
                uncertainty_score=claim.uncertainty,
                hold_flag=hold,
                fog_region=hold,
                domain_tags=[claim.claim_type, claim.support_status],
            )
        )
        if hold:
            fmm.mark_hold_region(cid)
        for route in routes:
            for rec_id in route.source_records:
                node_id = f"rec_{rec_id}"
                if node_id in fmm.nodes:
                    fmm.add_link(
                        FractalMemoryLink(
                            cid,
                            node_id,
                            "analogy" if route.route_type == "analogy" else "semantic",
                            strength=route.route_strength,
                            hold_flag=route.contradiction_present,
                            notes=route.route_type,
                        )
                    )
        for conflict in self.conflicts:
            a, b = f"rec_{conflict.record_a}", f"rec_{conflict.record_b}"
            if a in fmm.nodes and b in fmm.nodes:
                fmm.add_contradiction_link(a, b, notes=conflict.conflict_type)
        return fmm.to_dict()

    def export_dashboard(self) -> Path:
        return export_dashboard_summary(
            self.output_root / "dashboard_summary.json",
            sources=self.sources,
            records=self.records,
            claims=self.claims,
            routes=self.routes,
            conflicts=self.conflicts,
            guard_decisions=self.guard_decisions,
            lifecycle_records=self.lifecycle_records,
            audit_timeline=self.audit.read_all(),
        )

    def run_demo(self, samples_root: Path | None = None) -> dict[str, Any]:
        if samples_root is None:
            samples_root = Path(__file__).resolve().parents[2] / "guardian_authority" / "samples" / "corpus"
        for path in sorted(samples_root.glob("mock_*.json")):
            self.ingest(path)
        self.detect_conflicts()

        claims_path = samples_root / "user_claims.json"
        evaluations: list[dict[str, Any]] = []
        if claims_path.exists():
            for text in json.loads(claims_path.read_text(encoding="utf-8")).get("claims", []):
                evaluations.append(self.evaluate_claim(text))

        summary = {
            "sources": len(self.sources),
            "records": len(self.records),
            "claims_evaluated": len(evaluations),
            "conflicts": len(self.conflicts),
            "guard_decisions": self.guard_decisions,
            "doctrine": [
                "Authority is scoped evidence, not automatic truth.",
                "A citation route with valid scope/jurisdiction/version may support a scoped claim.",
                "A broken citation route produces WATCH or HOLD.",
            ],
        }
        _write_json(self.output_root / "authority_demo_summary.json", summary)
        md = self._demo_summary_md(summary, evaluations)
        (self.output_root / "authority_demo_summary.md").write_text(md, encoding="utf-8")
        self.export_dashboard()
        return summary

    def _demo_summary_md(self, summary: dict, evaluations: list[dict]) -> str:
        lines = [
            "# Guardian Authority Corpus Demo Summary",
            "",
            f"- Sources: {summary['sources']}",
            f"- Records: {summary['records']}",
            f"- Claims evaluated: {summary['claims_evaluated']}",
            f"- Conflicts: {summary['conflicts']}",
            "",
            "## Claim Evaluations",
            "",
        ]
        for ev in evaluations:
            claim = ev["claim"]
            lines.append(f"- **{claim.text[:60]}...** → {claim.support_status} / GUARD {claim.guard_recommendation}")
        lines.extend(["", "## Doctrine", ""])
        lines.extend(f"- {d}" for d in summary["doctrine"])
        return "\n".join(lines)

    def purge_demo(self) -> dict[str, Any]:
        if not self.lifecycle_records:
            raise RuntimeError("No lifecycle records. Run ingest or run-demo first.")
        target = self.lifecycle_records[0]
        target.lifecycle_state = "PURGE_PENDING"
        deleted: list[str] = []
        for key, path_str in list(target.derivative_artifacts.items()):
            path = Path(path_str)
            if path.exists() and "samples" not in str(path).replace("\\", "/"):
                if path.is_file():
                    path.unlink()
                    deleted.append(str(path))
                target.derivative_artifacts[key] = "[PURGED]"
        target.lifecycle_state = "PURGED"
        target.purge_completed_at = utc_now()
        target.purge_allowed = False
        self.audit.append(
            action="PURGED",
            actor="purge_demo",
            target=target.artifact_id,
            details={"deleted": deleted},
        )
        self._persist_corpus()
        self.export_dashboard()
        return {"artifact_id": target.artifact_id, "deleted_files": deleted, "final_state": "PURGED"}