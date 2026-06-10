"""Memory attractor creation and placement."""

from __future__ import annotations

from fractalish_ai.operational_self.models import CompressedMemory, MemoryAttractor, MemoryEvent, new_id
from fractalish_ai.operational_self.salience import (
    apply_components_to_attractor,
    basin_region_from_distance,
    compute_salience_components,
    compute_salience_score,
    distance_from_center,
)


def create_attractor(
    event: MemoryEvent,
    memory: CompressedMemory,
    *,
    override_region: str | None = None,
    override_status: str | None = None,
) -> MemoryAttractor:
    components = compute_salience_components(event, memory)
    salience = compute_salience_score(components)
    label = event.structured_summary[:80] or memory.compressed_summary[:80] or event.raw_summary[:80]

    is_scar = bool(memory.retained_scars) or "similarity means identity" in " ".join(memory.retained_claims).lower()
    is_fog = event.guard_status in ("HOLD", "REVERSE") and event.importance_hint < 0.6

    distance = distance_from_center(salience, is_scar=is_scar, is_fog=is_fog)
    region = override_region or basin_region_from_distance(distance, override="scar" if is_scar else ("fog" if is_fog else None))
    status = override_status or ("hold" if event.guard_status == "HOLD" else ("scarred" if is_scar else "active"))

    attractor = MemoryAttractor(
        attractor_id=new_id("attr"),
        memory_id=memory.memory_id,
        label=label,
        distance_from_reasoning_center=distance if region not in ("scar", "fog") else (0.25 if region == "scar" else 0.35),
        basin_region=region,  # type: ignore[arg-type]
        tags=list(event.tags),
        status=status,  # type: ignore[arg-type]
    )
    return apply_components_to_attractor(attractor, components, salience)