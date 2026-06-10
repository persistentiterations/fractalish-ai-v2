"""SessionGlyph — carry-forward activation state export."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SessionGlyph:
    activation_id: str
    purpose: str
    operator_constraints: list[str] = field(default_factory=list)
    open_loops: list[dict[str, Any]] = field(default_factory=list)
    unresolved_holds: list[dict[str, Any]] = field(default_factory=list)
    contradiction_scars: list[dict[str, Any]] = field(default_factory=list)
    recovery_routes: list[dict[str, Any]] = field(default_factory=list)
    key_sources: list[str] = field(default_factory=list)
    next_action: str = ""
    state_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def compute_hash(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def finalize(self) -> SessionGlyph:
        self.state_hash = self.compute_hash()
        return self


def build_session_glyph(
    *,
    activation_id: str,
    purpose: str,
    operator_constraints: list[str] | None,
    circuit: dict[str, Any],
    guard_decision: str,
    key_sources: list[str] | None = None,
) -> SessionGlyph:
    next_action = {
        "PROCEED": "Continue activation with recorded state.",
        "HOLD": "Pause; gather missing evidence before closure.",
        "REVERSE": "Revert to recovery route; reload constraints.",
        "WATCH": "Monitor with reduced commitment; log updates.",
    }.get(guard_decision, "Review activation state.")

    glyph = SessionGlyph(
        activation_id=activation_id,
        purpose=purpose,
        operator_constraints=operator_constraints or [],
        open_loops=circuit.get("open_loops", []),
        unresolved_holds=circuit.get("unresolved_holds", []),
        contradiction_scars=circuit.get("contradiction_scars", []),
        recovery_routes=circuit.get("recovery_routes", []),
        key_sources=key_sources or [],
        next_action=next_action,
    )
    return glyph.finalize()


def export_session_glyph(path: str, glyph: SessionGlyph) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(glyph.to_dict(), handle, indent=2)
    return path


def load_session_glyph(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def basin_from_glyph(glyph: dict[str, Any]) -> dict[str, Any]:
    """Reconstruct basin state from SessionGlyph for recovery demos."""
    return {
        "activation_id": glyph.get("activation_id", ""),
        "purpose": glyph.get("purpose", ""),
        "operator_constraints": glyph.get("operator_constraints", []),
        "circuit": {
            "memory_nodes": [],
            "contradiction_scars": glyph.get("contradiction_scars", []),
            "recovery_routes": glyph.get("recovery_routes", []),
            "trust_channels": {},
            "open_loops": glyph.get("open_loops", []),
            "unresolved_holds": glyph.get("unresolved_holds", []),
        },
        "session_glyph": glyph,
    }