"""BasinSimulationState — accumulated simulation trace."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BasinSimulationState:
    activation_id: str
    purpose: str = ""
    operator_constraints: list[str] = field(default_factory=list)
    current_focus: str = ""
    active_claims: list[str] = field(default_factory=list)
    percept_events: list[dict[str, Any]] = field(default_factory=list)
    atal_pressure: list[dict[str, Any]] = field(default_factory=list)
    rigor_findings: list[list[dict[str, Any]]] = field(default_factory=list)
    circuit_updates: list[dict[str, Any]] = field(default_factory=list)
    guard_decisions: list[dict[str, Any]] = field(default_factory=list)
    sera_records: list[dict[str, Any]] = field(default_factory=list)
    session_glyphs: list[dict[str, Any]] = field(default_factory=list)
    fractal_memory_map_snapshots: list[dict[str, Any]] = field(default_factory=list)
    unresolved_holds: list[dict[str, Any]] = field(default_factory=list)
    contradiction_scars: list[dict[str, Any]] = field(default_factory=list)
    recovery_routes: list[dict[str, Any]] = field(default_factory=list)
    scenario_history: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def latest_glyph(self) -> dict[str, Any]:
        return self.session_glyphs[-1] if self.session_glyphs else {}

    @property
    def latest_fmm(self) -> dict[str, Any]:
        return self.fractal_memory_map_snapshots[-1] if self.fractal_memory_map_snapshots else {}

    def record_step(
        self,
        *,
        scenario_name: str,
        record: dict[str, Any],
        fmm_snapshot: dict[str, Any],
        focus: str = "",
        claims: list[str] | None = None,
    ) -> None:
        self.scenario_history.append(scenario_name)
        if focus:
            self.current_focus = focus
        if claims:
            self.active_claims.extend(claims)
        self.percept_events.append(record.get("percept_token", {}))
        self.atal_pressure.append(record.get("atal_update", {}))
        self.rigor_findings.append(record.get("rigor_findings", []))
        self.circuit_updates.append(record.get("circuit_updates", {}))
        self.guard_decisions.append(record.get("guard_decision", {}))
        self.sera_records.append(record.get("sera_record", {}))
        glyph = record.get("updated_session_glyph", {})
        self.session_glyphs.append(glyph)
        self.fractal_memory_map_snapshots.append(fmm_snapshot)
        self.unresolved_holds = glyph.get("unresolved_holds", [])
        self.contradiction_scars = glyph.get("contradiction_scars", [])
        self.recovery_routes = glyph.get("recovery_routes", [])
        basin = record.get("updated_basin_state", {})
        self.purpose = basin.get("purpose", self.purpose)
        self.operator_constraints = basin.get("operator_constraints", self.operator_constraints)
        self.activation_id = glyph.get("activation_id", self.activation_id)