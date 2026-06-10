"""Transparent salience scoring for memory attractors."""

from __future__ import annotations

from fractalish_ai.operational_self.models import CompressedMemory, MemoryAttractor, MemoryEvent

DOCTRINE_TERMS = {
    "hold", "pressure is not truth", "similarity is not identity", "operator sovereignty",
    "memory is routed continuity", "govern before duplication",
}
CORE_MODULES = {
    "natural math", "cognitive basin", "guardian intake", "guardian authority", "operational self",
}


def compute_salience_components(event: MemoryEvent, memory: CompressedMemory) -> dict[str, float]:
    text = " ".join(
        [event.raw_summary, memory.compressed_summary, " ".join(memory.retained_claims), " ".join(event.tags)]
    ).lower()

    recurrence = min(1.0, sum(0.15 for t in event.tags if t in ("doctrine", "core", "commitment")))
    utility = min(1.0, event.importance_hint + (0.2 if event.source_type in ("cognitive_basin_run", "guardian_intake", "guardian_authority") else 0))
    contradiction = 0.8 if memory.retained_scars or event.guard_status in ("HOLD", "REVERSE") else 0.0
    if "similarity is not identity" in text or "similarity means identity" in text:
        contradiction = max(contradiction, 0.9)
    pressure = min(1.0, event.atal_pressure + event.emotional_or_pressure_load)
    authority = 0.7 if event.source_type == "guardian_authority" else 0.2
    recency = 0.8
    operator_anchor = 0.9 if "operator" in text or event.source_type == "operator_note" else 0.2
    replay_value = 0.7 if any(m in text for m in CORE_MODULES) else 0.3
    guard_weight = {"PROCEED": 0.2, "WATCH": 0.5, "HOLD": 0.8, "REVERSE": 0.9}.get(event.guard_status, 0.4)

    if any(d in text for d in DOCTRINE_TERMS):
        recurrence = max(recurrence, 0.85)
        utility = max(utility, 0.8)
    if any(m in text for m in CORE_MODULES):
        utility = max(utility, 0.75)
        replay_value = max(replay_value, 0.8)

    return {
        "recurrence_score": recurrence,
        "utility_score": utility,
        "contradiction_score": contradiction,
        "pressure_score": pressure,
        "authority_score": authority,
        "recency_score": recency,
        "operator_anchor_score": operator_anchor,
        "replay_value": replay_value,
        "guard_weight": guard_weight,
    }


def compute_salience_score(components: dict[str, float]) -> float:
    return min(
        1.0,
        components["recurrence_score"] * 0.18
        + components["utility_score"] * 0.18
        + components["replay_value"] * 0.14
        + components["operator_anchor_score"] * 0.12
        + components["authority_score"] * 0.08
        + components["recency_score"] * 0.08
        + components["guard_weight"] * 0.1
        + components["contradiction_score"] * 0.06
        + components["pressure_score"] * 0.06,
    )


def distance_from_center(salience: float, *, is_scar: bool = False, is_fog: bool = False) -> float:
    if is_scar:
        return 0.25
    if is_fog:
        return 0.35
    return max(0.0, min(1.0, 1.0 - salience))


def basin_region_from_distance(distance: float, *, override: str | None = None) -> str:
    if override:
        return override
    if distance <= 0.20:
        return "core"
    if distance <= 0.40:
        return "active"
    if distance <= 0.60:
        return "near"
    if distance <= 0.80:
        return "peripheral"
    return "dormant"


def apply_components_to_attractor(attractor: MemoryAttractor, components: dict[str, float], salience: float) -> MemoryAttractor:
    attractor.recurrence_score = components["recurrence_score"]
    attractor.utility_score = components["utility_score"]
    attractor.contradiction_score = components["contradiction_score"]
    attractor.pressure_score = components["pressure_score"]
    attractor.authority_score = components["authority_score"]
    attractor.recency_score = components["recency_score"]
    attractor.replay_value = components["replay_value"]
    attractor.salience_score = salience
    attractor.centrality_score = salience
    attractor.distance_from_reasoning_center = distance_from_center(salience)
    attractor.basin_region = basin_region_from_distance(attractor.distance_from_reasoning_center)  # type: ignore[assignment]
    return attractor