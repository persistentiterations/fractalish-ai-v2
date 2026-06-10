"""CIRCUIT — in-memory memory routes, scars, and open loops."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class MemoryNode:
    node_id: str
    label: str
    source: str
    content: str
    trust_weight: float = 0.5


@dataclass
class ContradictionScar:
    scar_id: str
    claim_a: str
    claim_b: str
    source_a: str
    source_b: str
    status: str = "unresolved"


@dataclass
class RecoveryRoute:
    route_id: str
    description: str
    next_step: str


@dataclass
class OpenLoop:
    loop_id: str
    description: str
    status: str = "open"


@dataclass
class UnresolvedHold:
    hold_id: str
    reason: str
    analyzer: str


@dataclass
class CircuitState:
    memory_nodes: list[MemoryNode] = field(default_factory=list)
    contradiction_scars: list[ContradictionScar] = field(default_factory=list)
    recovery_routes: list[RecoveryRoute] = field(default_factory=list)
    trust_channels: dict[str, float] = field(default_factory=dict)
    open_loops: list[OpenLoop] = field(default_factory=list)
    unresolved_holds: list[UnresolvedHold] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_nodes": [asdict(n) for n in self.memory_nodes],
            "contradiction_scars": [asdict(s) for s in self.contradiction_scars],
            "recovery_routes": [asdict(r) for r in self.recovery_routes],
            "trust_channels": dict(self.trust_channels),
            "open_loops": [asdict(l) for l in self.open_loops],
            "unresolved_holds": [asdict(h) for h in self.unresolved_holds],
        }


def circuit_from_dict(data: dict[str, Any] | None) -> CircuitState:
    data = data or {}
    circuit = CircuitState()
    for item in data.get("memory_nodes", []):
        circuit.memory_nodes.append(MemoryNode(**item))
    for item in data.get("contradiction_scars", []):
        circuit.contradiction_scars.append(ContradictionScar(**item))
    for item in data.get("recovery_routes", []):
        circuit.recovery_routes.append(RecoveryRoute(**item))
    for item in data.get("open_loops", []):
        circuit.open_loops.append(OpenLoop(**item))
    for item in data.get("unresolved_holds", []):
        circuit.unresolved_holds.append(UnresolvedHold(**item))
    circuit.trust_channels = dict(data.get("trust_channels", {}))
    return circuit


def update_circuit(
    circuit: CircuitState,
    *,
    percept: dict[str, Any],
    rigor_findings: list[dict[str, Any]],
    guard_decision: str,
) -> dict[str, Any]:
    updates: dict[str, Any] = {"added_nodes": [], "added_scars": [], "added_holds": [], "added_loops": []}

    circuit.memory_nodes.append(
        MemoryNode(
            node_id=percept["event_id"],
            label=percept.get("modality", "event"),
            source=percept.get("source", "unknown"),
            content=percept.get("content_summary", ""),
            trust_weight=percept.get("confidence", 0.5),
        )
    )
    updates["added_nodes"].append(percept["event_id"])

    meta = percept.get("provenance", {})
    for finding in rigor_findings:
        if finding["analyzer"] == "contradiction" and finding["state"] == "HOLD":
            scar = ContradictionScar(
                scar_id=f"scar-{percept['event_id'][:8]}",
                claim_a=meta.get("claim_a", finding.get("evidence_present", ["claim_a"])[0]),
                claim_b=meta.get("claim_b", finding.get("evidence_present", ["", "claim_b"])[1] if len(finding.get("evidence_present", [])) > 1 else "claim_b"),
                source_a=meta.get("source_a", percept.get("source", "unknown")),
                source_b=meta.get("source_b", "conflicting_source"),
            )
            circuit.contradiction_scars.append(scar)
            updates["added_scars"].append(scar.scar_id)

        if finding["state"] in ("HOLD", "WATCH"):
            hold = UnresolvedHold(
                hold_id=f"hold-{finding['analyzer']}-{percept['event_id'][:8]}",
                reason=finding["reason"],
                analyzer=finding["analyzer"],
            )
            circuit.unresolved_holds.append(hold)
            updates["added_holds"].append(hold.hold_id)

    if guard_decision in ("HOLD", "WATCH"):
        loop = OpenLoop(
            loop_id=f"loop-{percept['event_id'][:8]}",
            description=percept.get("content_summary", "unresolved activation step"),
        )
        circuit.open_loops.append(loop)
        updates["added_loops"].append(loop.loop_id)

    source = percept.get("source", "unknown")
    circuit.trust_channels[source] = percept.get("confidence", 0.5)

    if guard_decision == "REVERSE":
        circuit.recovery_routes.append(
            RecoveryRoute(
                route_id=f"recovery-{percept['event_id'][:8]}",
                description="Boundary violation detected; revert to prior safe state.",
                next_step="Reload SessionGlyph and re-validate constraints.",
            )
        )

    return updates