"""Salience decay simulation."""

from __future__ import annotations

from fractalish_ai.operational_self.models import MemoryAttractor
from fractalish_ai.operational_self.salience import basin_region_from_distance


PROTECTED_TAGS = {"doctrine", "core", "operator_anchor", "scar", "commitment"}


def apply_decay(attractors: dict[str, MemoryAttractor], *, steps: int = 3) -> list[dict]:
    log: list[dict] = []
    for _ in range(steps):
        for attr in attractors.values():
            if attr.basin_region in ("purged", "archived"):
                continue
            if attr.status in ("hold", "scarred"):
                log.append({"attractor_id": attr.attractor_id, "action": "preserved_hold_scar"})
                continue
            if PROTECTED_TAGS & set(attr.tags):
                log.append({"attractor_id": attr.attractor_id, "action": "preserved_core"})
                continue
            if attr.salience_score < 0.35:
                attr.salience_score = max(0.05, attr.salience_score - 0.08)
                attr.distance_from_reasoning_center = min(1.0, attr.distance_from_reasoning_center + 0.12)
                attr.basin_region = basin_region_from_distance(attr.distance_from_reasoning_center)  # type: ignore[assignment]
                if attr.distance_from_reasoning_center > 0.8:
                    attr.status = "deprecated"
                log.append({"attractor_id": attr.attractor_id, "action": "decayed_outward"})
    return log