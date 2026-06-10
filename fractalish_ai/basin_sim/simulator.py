"""BasinSimulation — coordinator for Cognitive Basin Simulation v1."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Callable

from fractalish_ai.basin_link import BasinLink, receptor_event_to_decision_record
from fractalish_ai.basin_sim.state import BasinSimulationState
from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.fractal_memory_map import FractalMemoryLink, FractalMemoryMap, FractalMemoryNode
from fractalish_ai.receptors import ReceptorEvent, create_receptor_event, to_percept_event
from fractalish_ai.session_glyph import basin_from_glyph

ScenarioFn = Callable[["BasinSimulation"], dict[str, Any]]


class BasinSimulation:
    """Run events through ReceptorEvent/PERCEPT → … → SessionGlyph with FractalMemoryMap."""

    def __init__(
        self,
        *,
        activation_id: str | None = None,
        purpose: str = "Cognitive Basin Simulation v1",
        operator_constraints: list[str] | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        self.activation_id = activation_id or f"basin-sim-{uuid.uuid4().hex[:12]}"
        self.purpose = purpose
        self.operator_constraints = operator_constraints or [
            "local_only",
            "hold_is_sacred",
            "pressure_not_truth",
            "similarity_not_identity",
            "mcva_not_proof",
        ]
        self.output_dir = Path(output_dir) if output_dir else None
        self.fmm = self._init_memory_map()
        self.state = BasinSimulationState(
            activation_id=self.activation_id,
            purpose=self.purpose,
            operator_constraints=list(self.operator_constraints),
        )
        self._basin_link = BasinLink(
            activation_id=self.activation_id,
            purpose=self.purpose,
            operator_constraints=self.operator_constraints,
            basin_state=default_basin_state(),
            fractal_memory_map=self.fmm.to_dict(),
        )
        self._basin_link.basin_state["activation_id"] = self.activation_id
        self._basin_link.basin_state["purpose"] = self.purpose
        self._basin_link.basin_state["operator_constraints"] = self.operator_constraints
        self._scenario_results: list[dict[str, Any]] = []

    def _init_memory_map(self) -> FractalMemoryMap:
        fmm = FractalMemoryMap(center_node_id="project_hub")
        fmm.add_node(
            FractalMemoryNode(
                node_id="project_hub",
                label="Cognitive Basin Simulation v1",
                salience=0.85,
                replay_score=0.5,
                current_distance_from_center=0.0,
                source="basin_sim@local",
                domain_tags=["project", "simulation"],
            )
        )
        fmm.add_node(
            FractalMemoryNode(
                node_id="fmm_contract",
                label="FractalMemoryMap contract",
                salience=0.75,
                replay_score=0.6,
                current_distance_from_center=0.35,
                source="spec@local",
                domain_tags=["fractal_memory_map", "contract"],
            )
        )
        fmm.add_link(
            FractalMemoryLink(
                source_node="project_hub",
                target_node="fmm_contract",
                relation_type="project",
                strength=0.8,
                replay_validated=True,
                notes="project semantic neighborhood",
            )
        )
        return fmm

    def _sync_circuit_to_fmm(
        self,
        record: dict[str, Any],
        *,
        node_id: str | None = None,
        label: str | None = None,
        domain_tags: list[str] | None = None,
        mark_hold: list[str] | None = None,
        contradiction_pair: tuple[str, str] | None = None,
        analogy_pair: tuple[str, str] | None = None,
        recovery_pair: tuple[str, str] | None = None,
        shortcut_pair: tuple[str, str] | None = None,
    ) -> None:
        """Mirror CIRCUIT records into FractalMemoryMap retrieval topology."""
        percept = record.get("percept_token", {})
        guard = record.get("guard_decision", {}).get("decision", "WATCH")
        glyph = record.get("updated_session_glyph", {})
        circuit = record.get("updated_basin_state", {}).get("circuit", {})

        nid = node_id or f"node-{percept.get('event_id', uuid.uuid4().hex)[:8]}"
        if nid not in self.fmm.nodes:
            replay = 0.5 if guard in ("PROCEED", "WATCH") else 0.2
            uncertainty = 0.3 if guard == "PROCEED" else 0.6
            self.fmm.add_node(
                FractalMemoryNode(
                    node_id=nid,
                    label=label or percept.get("content_summary", "activation node")[:80],
                    salience=0.6,
                    replay_score=replay,
                    current_distance_from_center=0.4,
                    uncertainty_score=uncertainty,
                    source=percept.get("source", "unknown"),
                    domain_tags=domain_tags or percept.get("domain_tags", []),
                )
            )
            if self.fmm.center_node_id and self.fmm.center_node_id in self.fmm.nodes:
                self.fmm.add_link(
                    FractalMemoryLink(
                        source_node=self.fmm.center_node_id,
                        target_node=nid,
                        relation_type="semantic",
                        strength=0.5,
                        replay_validated=guard == "PROCEED",
                    )
                )

        for scar in circuit.get("contradiction_scars", []):
            sa = f"scar-{scar.get('source_a', 'a')[:6]}"
            sb = f"scar-{scar.get('source_b', 'b')[:6]}"
            for sid, lbl, src in (
                (sa, scar.get("claim_a", "claim A"), scar.get("source_a", "a")),
                (sb, scar.get("claim_b", "claim B"), scar.get("source_b", "b")),
            ):
                if sid not in self.fmm.nodes:
                    self.fmm.add_node(
                        FractalMemoryNode(
                            node_id=sid,
                            label=lbl[:80],
                            salience=0.5,
                            contradiction_score=0.85,
                            uncertainty_score=0.7,
                            source=src,
                        )
                    )
            if sa in self.fmm.nodes and sb in self.fmm.nodes:
                existing = any(
                    l.relation_type == "contradiction"
                    and {l.source_node, l.target_node} == {sa, sb}
                    for l in self.fmm.links
                )
                if not existing:
                    self.fmm.add_contradiction_link(sa, sb, notes="circuit scar mirrored")

        for hold in glyph.get("unresolved_holds", []):
            hid = f"hold-{hold.get('analyzer', 'x')}"
            if hid not in self.fmm.nodes:
                self.fmm.add_node(
                    FractalMemoryNode(
                        node_id=hid,
                        label=hold.get("reason", "unresolved hold")[:80],
                        salience=0.4,
                        uncertainty_score=0.85,
                        hold_flag=True,
                    )
                )
            self.fmm.mark_hold_region(hid)

        if mark_hold:
            for mid in mark_hold:
                if mid not in self.fmm.nodes:
                    self.fmm.add_node(FractalMemoryNode(node_id=mid, label=mid, salience=0.4))
                self.fmm.mark_hold_region(mid)

        if contradiction_pair:
            a, b = contradiction_pair
            for x in (a, b):
                if x not in self.fmm.nodes:
                    self.fmm.add_node(FractalMemoryNode(node_id=x, label=x, salience=0.5))
            self.fmm.add_contradiction_link(a, b)

        if analogy_pair:
            a, b = analogy_pair
            for x in (a, b):
                if x not in self.fmm.nodes:
                    self.fmm.add_node(FractalMemoryNode(node_id=x, label=x, salience=0.5))
            self.fmm.add_link(
                FractalMemoryLink(
                    source_node=a,
                    target_node=b,
                    relation_type="analogy",
                    strength=0.55,
                    replay_validated=False,
                    notes="similarity — not identity",
                )
            )

        if recovery_pair:
            a, b = recovery_pair
            for x in (a, b):
                if x not in self.fmm.nodes:
                    self.fmm.add_node(FractalMemoryNode(node_id=x, label=x, salience=0.5))
            self.fmm.add_recovery_route(a, b, replay_validated=True)

        if shortcut_pair:
            a, b = shortcut_pair
            if a in self.fmm.nodes and b in self.fmm.nodes:
                self.fmm.add_link(
                    FractalMemoryLink(
                        source_node=a,
                        target_node=b,
                        relation_type="temporal",
                        strength=0.7,
                        replay_validated=True,
                        notes="long-range shortcut",
                    )
                )

        if guard in ("HOLD", "REVERSE") and nid in self.fmm.nodes:
            self.fmm.mark_hold_region(nid)

    def run_event(
        self,
        event: dict[str, Any] | ReceptorEvent,
        *,
        scenario_name: str = "event",
        fmm_node_id: str | None = None,
        fmm_label: str | None = None,
        fmm_domain_tags: list[str] | None = None,
        fmm_mark_hold: list[str] | None = None,
        fmm_contradiction: tuple[str, str] | None = None,
        fmm_analogy: tuple[str, str] | None = None,
        fmm_recovery: tuple[str, str] | None = None,
        fmm_shortcut: tuple[str, str] | None = None,
        focus: str = "",
        claims: list[str] | None = None,
    ) -> dict[str, Any]:
        if isinstance(event, ReceptorEvent):
            record = receptor_event_to_decision_record(event, self._basin_link)
            self._basin_link = BasinLink(
                activation_id=self._basin_link.activation_id,
                purpose=self._basin_link.purpose,
                operator_constraints=self._basin_link.operator_constraints,
                basin_state=record.get("updated_basin_state"),
                fractal_memory_map=self.fmm.to_dict(),
            )
        else:
            evt = dict(event)
            evt.setdefault("purpose", self.purpose)
            record = run_activation_event(evt, self._basin_link.basin_state)
            self._basin_link.basin_state = record.get("updated_basin_state", self._basin_link.basin_state)

        self._sync_circuit_to_fmm(
            record,
            node_id=fmm_node_id,
            label=fmm_label,
            domain_tags=fmm_domain_tags,
            mark_hold=fmm_mark_hold,
            contradiction_pair=fmm_contradiction,
            analogy_pair=fmm_analogy,
            recovery_pair=fmm_recovery,
            shortcut_pair=fmm_shortcut,
        )
        self._basin_link.fractal_memory_map = self.fmm.to_dict()

        attractors = self.fmm.nearest_active_attractors()
        fmm_snapshot = self.fmm.to_dict()
        fmm_snapshot["active_attractors"] = attractors

        self.state.record_step(
            scenario_name=scenario_name,
            record=record,
            fmm_snapshot=fmm_snapshot,
            focus=focus,
            claims=claims,
        )

        result = {
            "scenario": scenario_name,
            "guard_decision": record["guard_decision"]["decision"],
            "percept": record.get("percept_token"),
            "atal": record.get("atal_update"),
            "rigor_findings": record.get("rigor_findings"),
            "circuit_updates": record.get("circuit_updates"),
            "guard": record.get("guard_decision"),
            "sera": record.get("sera_record"),
            "session_glyph": record.get("updated_session_glyph"),
            "fractal_memory_map": fmm_snapshot,
            "active_attractors": attractors,
            "hold_regions": sorted(self.fmm.hold_regions),
        }
        return result

    def run_scenario(self, name: str, fn: ScenarioFn) -> dict[str, Any]:
        result = fn(self)
        result["scenario_name"] = name
        self._scenario_results.append(result)
        return result

    def run_all_scenarios(self, scenarios: list[tuple[str, ScenarioFn]]) -> list[dict[str, Any]]:
        self._scenario_results.clear()
        for name, fn in scenarios:
            self.run_scenario(name, fn)
        return list(self._scenario_results)

    def load_from_glyph_and_fmm(
        self,
        glyph: dict[str, Any],
        fmm_data: dict[str, Any],
    ) -> None:
        """Recovery path — reload SessionGlyph + FractalMemoryMap only."""
        recovered = basin_from_glyph(glyph)
        self._basin_link.basin_state = recovered
        self._basin_link.activation_id = glyph.get("activation_id", self.activation_id)
        self.fmm = FractalMemoryMap.from_dict(fmm_data)
        self.state.activation_id = glyph.get("activation_id", self.activation_id)
        self.state.purpose = glyph.get("purpose", self.purpose)
        self.state.unresolved_holds = glyph.get("unresolved_holds", [])
        self.state.contradiction_scars = glyph.get("contradiction_scars", [])
        self.state.recovery_routes = glyph.get("recovery_routes", [])

    def build_summary(self) -> dict[str, Any]:
        guards = [r.get("guard_decision", r.get("guard", {}).get("decision", "?")) for r in self._scenario_results]
        counts = {"PROCEED": 0, "HOLD": 0, "WATCH": 0, "REVERSE": 0}
        for g in guards:
            if isinstance(g, dict):
                g = g.get("decision", "?")
            counts[g] = counts.get(g, 0) + 1

        fmm = self.fmm.to_dict()
        link_counts = {
            "analogy": sum(1 for l in self.fmm.links if l.relation_type == "analogy"),
            "contradiction": sum(1 for l in self.fmm.links if l.relation_type == "contradiction"),
            "recovery": sum(1 for l in self.fmm.links if l.relation_type == "recovery"),
        }
        sera_totals = {
            "runtime_ms": sum(s.get("runtime_ms", 0) for s in self.state.sera_records),
            "hold_count": sum(s.get("hold_count", 0) for s in self.state.sera_records),
            "unsupported_claim_count": sum(s.get("unsupported_claim_count", 0) for s in self.state.sera_records),
        }

        return {
            "simulation": "cognitive_basin_sim_v1",
            "doctrine": (
                "Natural Math generates process. "
                "Fractalish reads the shape left by process. "
                "Cognitive Basin preserves reasoning state across process."
            ),
            "scenarios_run": [r["scenario_name"] for r in self._scenario_results],
            "scenario_results": [
                {
                    "name": r["scenario_name"],
                    "guard": r.get("guard_decision"),
                    "assertions_passed": r.get("assertions_passed", True),
                }
                for r in self._scenario_results
            ],
            "guard_counts": counts,
            "contradiction_scars": len(self.state.contradiction_scars),
            "unresolved_holds": len(self.state.unresolved_holds),
            "recovery_routes": len(self.state.recovery_routes),
            "hold_fog_regions": sorted(self.fmm.hold_regions),
            "active_attractors": self.fmm.nearest_active_attractors(),
            "link_counts": link_counts,
            "sera_summary": sera_totals,
            "final_session_glyph_hash": self.state.latest_glyph.get("state_hash", ""),
            "final_session_glyph": self.state.latest_glyph,
            "fractal_memory_map": fmm,
        }

    def write_outputs(self, output_dir: str | Path | None = None) -> Path:
        from fractalish_ai.basin_sim.report import write_all_outputs

        out = Path(output_dir or self.output_dir or ".")
        write_all_outputs(out, self._scenario_results, self.build_summary(), self.state)
        return out