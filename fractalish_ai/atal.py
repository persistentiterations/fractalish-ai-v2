"""ATAL — pressure field tracking without emotion simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AtalState:
    coherence: float = 0.5
    uncertainty: float = 0.5
    threat: float = 0.0
    trust: float = 0.5
    fatigue: float = 0.0
    frustration: float = 0.0
    curiosity: float = 0.3
    boundary_integrity: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def update_atal(
    state: AtalState,
    *,
    confidence: float,
    uncertainty: float,
    hold_count: int = 0,
    contradiction_count: int = 0,
    boundary_violation: bool = False,
) -> AtalState:
    """Adjust pressure fields from percept and rigor signals. Does not decide truth."""
    state.uncertainty = 0.6 * state.uncertainty + 0.4 * uncertainty
    state.coherence = 0.6 * state.coherence + 0.4 * confidence
    state.threat = min(1.0, state.threat + 0.15 * contradiction_count)
    state.frustration = min(1.0, state.frustration + 0.1 * hold_count)
    state.fatigue = min(1.0, state.fatigue + 0.02)
    state.curiosity = max(0.0, state.curiosity - 0.05 * hold_count + 0.02)
    if boundary_violation:
        state.boundary_integrity = max(0.0, state.boundary_integrity - 0.4)
        state.threat = min(1.0, state.threat + 0.3)
    state.trust = max(0.0, min(1.0, state.trust + 0.1 * confidence - 0.15 * uncertainty))
    return state