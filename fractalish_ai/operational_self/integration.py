"""Integration with FractalMemoryMap, SessionGlyph, Guardian layers."""

from __future__ import annotations

from typing import Any

from fractalish_ai.fractal_memory_map import FractalMemoryMap, FractalMemoryLink, FractalMemoryNode
from fractalish_ai.operational_self.models import (
    CompressedMemory,
    ContradictionScar,
    FogRegion,
    MemoryAttractor,
    MemoryLink,
    OperationalSelfState,
    ReplayRoute,
    SelfNarrativeFrame,
)
from fractalish_ai.session_glyph import SessionGlyph


LINK_TYPE_TO_RELATION = {
    "contradicts": "contradiction",
    "recovery_route": "recovery",
    "same_project": "project",
    "session_continuity": "temporal",
    "authority_route": "semantic",
    "guardian_route": "semantic",
    "operator_anchor": "operator",
    "supports": "semantic",
    "elaborates": "semantic",
    "depends_on": "causal",
    "analogy": "analogy",
}


def build_fractal_memory_map_snapshot(
    attractors: dict[str, MemoryAttractor],
    memories: dict[str, CompressedMemory],
    links: list[MemoryLink],
    scars: list[ContradictionScar],
    fog_regions: list[FogRegion],
    replay_routes: list[ReplayRoute],
) -> dict[str, Any]:
    fmm = FractalMemoryMap(center_node_id="reasoning_center")
    fmm.add_node(
        FractalMemoryNode(
            node_id="reasoning_center",
            label="Reasoning Center",
            salience=1.0,
            current_distance_from_center=0.0,
            domain_tags=["operational_self", "core"],
            source="operational_self",
        )
    )

    node_map: dict[str, str] = {}
    for attr in attractors.values():
        nid = f"node_{attr.attractor_id}"
        node_map[attr.memory_id] = nid
        mem = memories.get(attr.memory_id)
        fmm.add_node(
            FractalMemoryNode(
                node_id=nid,
                label=attr.label[:80],
                salience=attr.salience_score,
                current_distance_from_center=attr.distance_from_reasoning_center,
                replay_score=attr.replay_value,
                contradiction_score=attr.contradiction_score,
                uncertainty_score=1.0 - attr.salience_score,
                domain_tags=attr.tags,
                source=mem.source_event_id if mem else "",
                hold_flag=attr.status == "hold" or attr.basin_region == "fog",
                fog_region=attr.basin_region == "fog",
            )
        )
        if attr.basin_region in ("core", "active"):
            fmm.add_link(
                FractalMemoryLink(
                    "reasoning_center", nid, "semantic",
                    strength=attr.salience_score,
                    notes=f"basin_region={attr.basin_region}",
                )
            )
        if attr.basin_region == "fog":
            fmm.mark_hold_region(nid)

    for link in links:
        src = node_map.get(link.from_memory_id)
        tgt = node_map.get(link.to_memory_id)
        if src and tgt:
            rel = LINK_TYPE_TO_RELATION.get(link.link_type, "semantic")
            if link.link_type == "contradicts":
                fmm.add_contradiction_link(src, tgt, strength=link.strength, notes=link.reason)
            elif link.link_type == "recovery_route":
                fmm.add_recovery_route(src, tgt, notes=link.reason)
            else:
                fmm.add_link(FractalMemoryLink(src, tgt, rel, strength=link.strength, notes=link.reason))

    for scar in scars:
        if len(scar.memory_ids) >= 2:
            a, b = scar.memory_ids[0], scar.memory_ids[1]
            if a in node_map and b in node_map:
                fmm.add_contradiction_link(node_map[a], node_map[b], notes=scar.replay_warning)

    for fog in fog_regions:
        for mid in fog.related_memory_ids:
            if mid in node_map:
                fmm.mark_hold_region(node_map[mid])

    for route in replay_routes:
        if len(route.memory_path) >= 2:
            src = node_map.get(route.memory_path[0])
            tgt = node_map.get(route.memory_path[-1])
            if src and tgt:
                fmm.add_recovery_route(src, tgt, notes=route.recommended_next_action)

    snapshot = fmm.to_dict()
    snapshot["operational_self_layer"] = "fractal_attractor_memory_v0.1"
    snapshot["fog_region_count"] = len(fog_regions)
    snapshot["scar_count"] = len(scars)
    return snapshot


def build_session_glyph_update(
    state: OperationalSelfState,
    frame: SelfNarrativeFrame,
    attractors: dict[str, MemoryAttractor],
    scars: list[ContradictionScar],
    replay_routes: list[ReplayRoute],
) -> dict[str, Any]:
    glyph = SessionGlyph(
        activation_id=state.activation_id,
        purpose=state.purpose,
        operator_constraints=state.operator_constraints,
        open_loops=[{"loop": l} for l in state.unresolved_loops],
        unresolved_holds=[{"region": h} for h in state.hold_regions],
        contradiction_scars=[s.to_dict() for s in scars],
        recovery_routes=[r.to_dict() for r in replay_routes],
        key_sources=state.recent_memory_ids[:5],
        next_action=frame.next_actions[0] if frame.next_actions else "Continue activation.",
    ).finalize()

    payload = glyph.to_dict()
    payload["active_focus"] = state.active_focus
    payload["active_attractors"] = [
        attractors[aid].to_dict() for aid in state.active_attractors if aid in attractors
    ][:10]
    payload["operational_self_id"] = state.self_id
    payload["non_claims"] = state.non_claims
    return payload