"""Replay route construction."""

from __future__ import annotations

from fractalish_ai.operational_self.models import (
    CompressedMemory,
    ContradictionScar,
    FogRegion,
    MemoryAttractor,
    ReplayRoute,
    new_id,
)

BUILD_SEQUENCE = [
    "natural math",
    "cognitive basin",
    "guardian intake",
    "guardian authority",
    "operational self",
]


def build_replay_route(
    label: str,
    memories: dict[str, CompressedMemory],
    attractors: dict[str, MemoryAttractor],
    scars: list[ContradictionScar],
    fog_regions: list[FogRegion],
) -> ReplayRoute | None:
    lower = label.lower()
    if "resume" not in lower and "product build" not in lower and "build" not in lower:
        return None

    path: list[str] = []
    for keyword in BUILD_SEQUENCE:
        for mem_id, mem in memories.items():
            text = mem.compressed_summary.lower()
            if keyword in text:
                path.append(mem_id)
                break

    if not path:
        ranked = sorted(attractors.values(), key=lambda a: a.salience_score, reverse=True)
        path = [a.memory_id for a in ranked[:5]]

    if not path:
        return None

    holds = [f.fog_id for f in fog_regions if f.guard_status == "HOLD"]
    warnings = [s.replay_warning for s in scars if s.replay_warning]

    return ReplayRoute(
        route_id=new_id("replay"),
        label=label,
        start_memory_id=path[0],
        target_memory_id=path[-1],
        memory_path=path,
        required_context=["prior build state", "unresolved HOLDs", "doctrine constraints"],
        unresolved_holds=holds,
        contradiction_warnings=warnings,
        recommended_next_action="Continue Operational Self + Fractal Attractor Memory integration; preserve prior modules.",
        confidence=0.75,
        uncertainty=0.25,
    )