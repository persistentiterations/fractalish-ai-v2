"""BasinLink — bridge ReceptorEvent into PERCEPT and Cognitive Basin runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.receptors import ReceptorEvent, to_percept_event


@dataclass
class BasinLink:
    activation_id: str
    purpose: str = ""
    operator_constraints: list[str] = field(default_factory=list)
    basin_state: dict[str, Any] | None = None
    fractal_memory_map: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def bind_receptor_to_basin(
    receptor: ReceptorEvent,
    link: BasinLink | None = None,
) -> tuple[dict[str, Any], BasinLink]:
    """Convert ReceptorEvent to PERCEPT-compatible event; preserve activation continuity."""
    percept_event = to_percept_event(receptor)
    basin = link.basin_state if link and link.basin_state else default_basin_state()

    if link:
        basin["activation_id"] = link.activation_id
        if link.purpose:
            basin["purpose"] = link.purpose
        if link.operator_constraints:
            basin["operator_constraints"] = link.operator_constraints
        percept_event["purpose"] = basin.get("purpose", link.purpose)

    updated_link = BasinLink(
        activation_id=basin.get("activation_id", link.activation_id if link else basin["activation_id"]),
        purpose=basin.get("purpose", ""),
        operator_constraints=basin.get("operator_constraints", []),
        basin_state=basin,
        fractal_memory_map=link.fractal_memory_map if link else None,
    )
    return percept_event, updated_link


def receptor_event_to_decision_record(
    receptor: ReceptorEvent,
    link: BasinLink | None = None,
) -> dict[str, Any]:
    """Full path: ReceptorEvent → PERCEPT event → existing basin runtime."""
    percept_event, updated_link = bind_receptor_to_basin(receptor, link)
    record = run_activation_event(percept_event, updated_link.basin_state)
    updated_link.basin_state = record.get("updated_basin_state", updated_link.basin_state)
    record["basin_link"] = updated_link.to_dict()
    record["receptor_event"] = receptor.to_dict()
    record["percept_input_event"] = percept_event
    return record