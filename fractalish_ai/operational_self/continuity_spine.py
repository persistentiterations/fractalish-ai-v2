"""Operational Self continuity spine — main consolidation pipeline."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fractalish_ai.operational_self.attractors import create_attractor
from fractalish_ai.operational_self.audit import OperationalSelfAuditLog
from fractalish_ai.operational_self.compression import light_compress
from fractalish_ai.operational_self.dashboard_export import export_dashboard
from fractalish_ai.operational_self.decay import apply_decay
from fractalish_ai.operational_self.fog import detect_fog_from_event
from fractalish_ai.operational_self.integration import (
    build_fractal_memory_map_snapshot,
    build_session_glyph_update,
)
from fractalish_ai.operational_self.memory_ingestion import ingest_file
from fractalish_ai.operational_self.models import (
    MemoryEvent,
    MemoryLink,
    OperationalSelfSnapshot,
    new_id,
    utc_now,
)
from fractalish_ai.operational_self.replay import build_replay_route
from fractalish_ai.operational_self.retrieval import retrieve
from fractalish_ai.operational_self.scars import detect_scars_from_event
from fractalish_ai.operational_self.self_state import (
    create_initial_self,
    update_narrative_frame,
    update_self_from_consolidation,
)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


class OperationalSelfEngine:
    """Local-first operational self + fractal attractor memory engine."""

    def __init__(self, output_root: Path | None = None) -> None:
        if output_root is None:
            output_root = Path(__file__).resolve().parents[2] / "operational_self" / "outputs"
        self.output_root = Path(output_root)
        self.activation_id = f"act-{uuid.uuid4().hex[:12]}"
        self.events: list[MemoryEvent] = []
        self.memories: dict[str, Any] = {}
        self.attractors: dict[str, Any] = {}
        self.links: list[Any] = []
        self.scars: list[Any] = []
        self.fog_regions: list[Any] = []
        self.replay_routes: list[Any] = []
        self.self_state = create_initial_self(activation_id=self.activation_id)
        self.narrative_frame = None
        self.decay_log: list[dict] = []
        self.retrieval_samples: list[dict] = []
        self.fmm_snapshot: dict[str, Any] = {}
        self.session_glyph: dict[str, Any] = {}
        self.audit = OperationalSelfAuditLog(self.output_root / "audit.jsonl")
        self._project_id = "fractalish-ai"
        self._last_bundle: dict[str, Any] = {}

    def _link_events(self, prev_memory_id: str | None, memory_id: str, event: MemoryEvent) -> None:
        if prev_memory_id:
            self.links.append(
                MemoryLink(
                    link_id=new_id("link"),
                    from_memory_id=prev_memory_id,
                    to_memory_id=memory_id,
                    link_type="session_continuity",
                    strength=0.7,
                    reason="Sequential session consolidation",
                )
            )
        if event.source_type == "guardian_intake":
            self.links.append(
                MemoryLink(
                    link_id=new_id("link"),
                    from_memory_id=memory_id,
                    to_memory_id=memory_id,
                    link_type="guardian_route",
                    strength=0.8,
                    reason="Guardian intake governed route",
                    evidence=[event.provenance.get("lifecycle_state", "")],
                )
            )
        if event.source_type == "guardian_authority":
            self.links.append(
                MemoryLink(
                    link_id=new_id("link"),
                    from_memory_id=memory_id,
                    to_memory_id=memory_id,
                    link_type="authority_route",
                    strength=0.75,
                    reason="Authority citation route",
                    evidence=[
                        str(event.provenance.get("jurisdiction", "")),
                        str(event.provenance.get("version", "")),
                        str(event.provenance.get("scope", "")),
                    ],
                )
            )

    def consolidate_event(self, event: MemoryEvent, prev_memory_id: str | None = None) -> dict[str, Any]:
        memory = light_compress(event)
        attractor = create_attractor(event, memory)
        event_scars = detect_scars_from_event(event, memory)
        fog = detect_fog_from_event(event, memory)

        if fog:
            attractor.basin_region = "fog"
            attractor.status = "hold"
            attractor.distance_from_reasoning_center = 0.35
            self.fog_regions.append(fog)

        if event_scars:
            for scar in event_scars:
                attractor.basin_region = "scar"
                attractor.status = "scarred"
                self.scars.append(scar)

        self.memories[memory.memory_id] = memory
        self.attractors[attractor.attractor_id] = attractor
        self._link_events(prev_memory_id, memory.memory_id, event)

        route = build_replay_route("resume product build", self.memories, self.attractors, self.scars, self.fog_regions)
        if route and not any(r.route_id == route.route_id for r in self.replay_routes):
            self.replay_routes.append(route)

        self.self_state = update_self_from_consolidation(
            self.self_state, event, memory, attractor, event_scars, fog, self.replay_routes
        )
        self.audit.append(
            action="CONSOLIDATE",
            actor="continuity_spine",
            target=memory.memory_id,
            details={"source_type": event.source_type, "basin_region": attractor.basin_region},
        )
        return {"event": event, "memory": memory, "attractor": attractor, "scars": event_scars, "fog": fog}

    def ingest_bundle(self, path: Path) -> dict[str, Any]:
        bundle, events = ingest_file(path)
        self._last_bundle = bundle
        if bundle.get("activation_id"):
            self.activation_id = bundle["activation_id"]
            self.self_state.activation_id = self.activation_id
        if bundle.get("project_id"):
            self._project_id = bundle["project_id"]
            self.self_state.project_id = self._project_id
        if bundle.get("purpose"):
            self.self_state.purpose = bundle["purpose"]
        if bundle.get("operator_constraints"):
            self.self_state.operator_constraints = bundle["operator_constraints"]

        prev_id: str | None = self.self_state.recent_memory_ids[0] if self.self_state.recent_memory_ids else None
        results = []
        for event in events:
            self.events.append(event)
            r = self.consolidate_event(event, prev_id)
            prev_id = r["memory"].memory_id
            results.append(r)

        self.narrative_frame = update_narrative_frame(self.narrative_frame, self.self_state, events)
        self._persist()
        return {"bundle": bundle, "events_ingested": len(events), "results": results}

    def ingest_session(self, path: Path) -> dict[str, Any]:
        return self.ingest_bundle(path)

    def ingest_guardian(self, path: Path) -> dict[str, Any]:
        return self.ingest_bundle(path)

    def ingest_authority(self, path: Path) -> dict[str, Any]:
        return self.ingest_bundle(path)

    def _build_snapshot(self) -> OperationalSelfSnapshot:
        core = [a.to_dict() for a in self.attractors.values() if a.basin_region == "core"]
        active = [a.to_dict() for a in self.attractors.values() if a.basin_region in ("core", "active")]
        snap = OperationalSelfSnapshot(
            snapshot_id=new_id("snap"),
            self_state=self.self_state.to_dict(),
            narrative_frame=self.narrative_frame.to_dict() if self.narrative_frame else {},
            core_attractors=core,
            active_attractors=active,
            fog_regions=[f.to_dict() for f in self.fog_regions],
            contradiction_scars=[s.to_dict() for s in self.scars],
            replay_routes=[r.to_dict() for r in self.replay_routes],
            memory_counts={
                "events": len(self.events),
                "memories": len(self.memories),
                "attractors": len(self.attractors),
                "links": len(self.links),
                "scars": len(self.scars),
                "fog_regions": len(self.fog_regions),
            },
            integrity_warnings=self._integrity_warnings(),
            created_at=utc_now(),
        ).finalize()
        return snap

    def _integrity_warnings(self) -> list[str]:
        warnings: list[str] = []
        if not self.self_state.non_claims:
            warnings.append("Missing non_claims boundary markers")
        if any("similarity means identity" in m.compressed_summary.lower() for m in self.memories.values()):
            warnings.append("Potential similarity/identity collapse detected")
        return warnings

    def _persist(self) -> None:
        self.fmm_snapshot = build_fractal_memory_map_snapshot(
            self.attractors, self.memories, self.links, self.scars, self.fog_regions, self.replay_routes
        )
        if self.narrative_frame:
            self.session_glyph = build_session_glyph_update(
                self.self_state, self.narrative_frame, self.attractors, self.scars, self.replay_routes
            )
            self.self_state.session_glyph_refs = [self.session_glyph.get("state_hash", "")]
        snapshot = self._build_snapshot()

        _write_json(self.output_root / "memory_events.json", [e.to_dict() for e in self.events])
        _write_json(self.output_root / "compressed_memories.json", [m.to_dict() for m in self.memories.values()])
        _write_json(self.output_root / "memory_attractors.json", [a.to_dict() for a in self.attractors.values()])
        _write_json(self.output_root / "memory_links.json", [l.to_dict() for l in self.links])
        _write_json(self.output_root / "contradiction_scars.json", [s.to_dict() for s in self.scars])
        _write_json(self.output_root / "fog_regions.json", [f.to_dict() for f in self.fog_regions])
        _write_json(self.output_root / "replay_routes.json", [r.to_dict() for r in self.replay_routes])
        _write_json(self.output_root / "self_state.json", self.self_state.to_dict())
        if self.narrative_frame:
            _write_json(self.output_root / "self_narrative_frame.json", self.narrative_frame.to_dict())
        _write_json(self.output_root / "operational_self_snapshot.json", snapshot.to_dict())
        _write_json(self.output_root / "fractal_memory_map_snapshot.json", self.fmm_snapshot)
        _write_json(self.output_root / "session_glyph_update.json", self.session_glyph)

    def retrieve_query(self, query: str) -> dict:
        result = retrieve(
            query,
            memories=self.memories,
            attractors=self.attractors,
            links=self.links,
            scars=self.scars,
        )
        self.retrieval_samples.append(result)
        return result

    def replay_route(self, label: str) -> dict:
        route = build_replay_route(label, self.memories, self.attractors, self.scars, self.fog_regions)
        if route:
            if not any(r.route_id == route.route_id for r in self.replay_routes):
                self.replay_routes.append(route)
            self._persist()
            return route.to_dict()
        existing = self.replay_routes[0].to_dict() if self.replay_routes else {}
        return existing

    def decay_demo(self) -> dict:
        self.decay_log = apply_decay(self.attractors)
        self._persist()
        return {"decay_steps": 3, "log": self.decay_log}

    def purge_demo(self) -> dict:
        candidates = [
            a for a in self.attractors.values()
            if a.basin_region not in ("core", "scar")
            and "doctrine" not in a.tags
            and "core" not in a.tags
            and "operator_anchor" not in a.tags
        ]
        if not candidates:
            candidates = [a for a in self.attractors.values() if a.basin_region == "dormant"]
        if not candidates:
            return {"error": "No purge candidate"}

        target = candidates[0]
        target.basin_region = "purged"
        target.status = "purged"
        target.salience_score = 0.0
        self.audit.append(
            action="PURGED",
            actor="purge_demo",
            target=target.memory_id,
            details={"attractor_id": target.attractor_id},
        )
        self._persist()
        return {"purged_memory_id": target.memory_id, "basin_region": "purged", "doctrine_preserved": True}

    def export_dashboard(self) -> Path:
        path = export_dashboard(
            self.output_root / "dashboard_summary.json",
            self_state=self.self_state.to_dict(),
            narrative_frame=self.narrative_frame.to_dict() if self.narrative_frame else {},
            attractors=[a.to_dict() for a in self.attractors.values()],
            memories=[m.to_dict() for m in self.memories.values()],
            links=[l.to_dict() for l in self.links],
            scars=[s.to_dict() for s in self.scars],
            fog_regions=[f.to_dict() for f in self.fog_regions],
            replay_routes=[r.to_dict() for r in self.replay_routes],
            fmm_snapshot=self.fmm_snapshot,
            retrieval_samples=self.retrieval_samples,
            decay_log=self.decay_log,
            audit_timeline=self.audit.read_all(),
        )
        return path

    def run_demo(self, samples_root: Path | None = None) -> dict[str, Any]:
        if samples_root is None:
            samples_root = Path(__file__).resolve().parents[2] / "operational_self" / "samples"

        paths = [
            samples_root / "session_events" / "fractalish_build_session.json",
            samples_root / "guardian_events" / "guardian_intake_summary.json",
            samples_root / "authority_events" / "authority_claim_summary.json",
            samples_root / "chat_turns" / "operational_self_discussion.json",
        ]
        for p in paths:
            if p.exists():
                self.ingest_bundle(p)

        self.retrieve_query("Guardian Intake")
        self.retrieve_query("pressure is not truth")
        self.retrieve_query("similarity means identity")
        route = self.replay_route("resume product build")
        decay = self.decay_demo()

        summary = {
            "events": len(self.events),
            "memories": len(self.memories),
            "core_attractors": len([a for a in self.attractors.values() if a.basin_region == "core"]),
            "scars": len(self.scars),
            "fog_regions": len(self.fog_regions),
            "replay_route": route.get("route_id", ""),
            "decay_actions": len(decay.get("log", [])),
            "doctrine": [
                "Operational self is continuity-bearing structure, not consciousness.",
                "Memory is routed continuity.",
                "HOLD remains sacred.",
            ],
        }
        _write_json(self.output_root / "demo_summary.json", summary)
        (self.output_root / "demo_summary.md").write_text(self._demo_md(summary), encoding="utf-8")
        self.export_dashboard()
        return summary

    def _demo_md(self, summary: dict) -> str:
        lines = [
            "# Operational Self Demo Summary",
            "",
            f"- Events: {summary['events']}",
            f"- Memories: {summary['memories']}",
            f"- Core attractors: {summary['core_attractors']}",
            f"- Scars: {summary['scars']}",
            f"- Fog regions: {summary['fog_regions']}",
            "",
            "## Doctrine",
        ]
        lines.extend(f"- {d}" for d in summary["doctrine"])
        return "\n".join(lines)