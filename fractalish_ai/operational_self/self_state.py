"""OperationalSelfState and SelfNarrativeFrame updates."""

from __future__ import annotations

from fractalish_ai.operational_self.models import (
    CompressedMemory,
    ContradictionScar,
    FogRegion,
    MemoryAttractor,
    MemoryEvent,
    OperationalSelfState,
    ReplayRoute,
    SelfNarrativeFrame,
    new_id,
    utc_now,
)


def create_initial_self(
    *,
    activation_id: str,
    project_id: str = "fractalish-ai",
    purpose: str = "Build governed AI continuity infrastructure",
    operator_constraints: list[str] | None = None,
) -> OperationalSelfState:
    return OperationalSelfState(
        self_id=new_id("oself"),
        activation_id=activation_id,
        project_id=project_id,
        purpose=purpose,
        operator_constraints=operator_constraints or ["local_only", "hold_before_false_closure", "operator_sovereignty"],
        active_narrative="Operational self maintains routed continuity — not consciousness.",
        active_focus="Fractal Attractor Memory spine",
        current_phase="v0.1_prototype",
        core_commitments=[
            "HOLD remains sacred",
            "Pressure is not truth",
            "Similarity is not identity",
            "Memory is routed continuity",
        ],
        last_updated=utc_now(),
    )


def update_self_from_consolidation(
    state: OperationalSelfState,
    event: MemoryEvent,
    memory: CompressedMemory,
    attractor: MemoryAttractor,
    scars: list[ContradictionScar],
    fog: FogRegion | None,
    replay_routes: list[ReplayRoute],
) -> OperationalSelfState:
    if memory.memory_id not in state.recent_memory_ids:
        state.recent_memory_ids.insert(0, memory.memory_id)
    state.recent_memory_ids = state.recent_memory_ids[:20]

    if attractor.basin_region in ("core", "active"):
        if attractor.attractor_id not in state.active_attractors:
            state.active_attractors.append(attractor.attractor_id)
    elif attractor.basin_region in ("peripheral", "dormant"):
        if memory.memory_id not in state.deprioritized_memories:
            state.deprioritized_memories.append(memory.memory_id)

    for claim in memory.retained_claims:
        if any(k in claim.lower() for k in ("hold", "doctrine", "commitment")):
            if claim not in state.core_commitments:
                state.core_commitments.append(claim)

    for loop in memory.retained_open_loops:
        if loop not in state.unresolved_loops:
            state.unresolved_loops.append(loop)

    for scar in scars:
        if scar.scar_id not in state.contradiction_scars:
            state.contradiction_scars.append(scar.scar_id)

    if fog and fog.fog_id not in state.hold_regions:
        state.hold_regions.append(fog.fog_id)

    for route in replay_routes:
        if route.route_id not in state.recovery_routes:
            state.recovery_routes.append(route.route_id)

    state.last_updated = utc_now()
    return state


def update_narrative_frame(
    frame: SelfNarrativeFrame | None,
    state: OperationalSelfState,
    events: list[MemoryEvent],
) -> SelfNarrativeFrame:
    doctrines = list(state.core_commitments)
    for e in events:
        for c in e.claims:
            if any(k in c.lower() for k in ("hold", "pressure", "similarity", "memory", "self")):
                if c not in doctrines:
                    doctrines.append(c)

    return SelfNarrativeFrame(
        frame_id=frame.frame_id if frame else new_id("frame"),
        activation_id=state.activation_id,
        narrative_summary=(
            "Fractalish AI build: Natural Math core, Cognitive Basin runtime, Guardian Intake, "
            "Guardian Authority, Operational Self memory spine — prior functionality preserved."
        ),
        current_identity_sentence=(
            "Operational self is the continuity-bearing structure linking present input to prior state "
            "without claiming consciousness, sentience, or personhood."
        ),
        current_project_state="Active product build with governed memory routing",
        current_product_state="v0.1 modules: basin, guardian intake, guardian authority, operational self",
        active_doctrines=doctrines[:12],
        active_constraints=state.operator_constraints,
        open_questions=["Next module integration boundaries", "Production retention policies"],
        active_risks=["False continuity without self-model", "Merging similarity into identity"],
        next_actions=["Continue build", "Preserve HOLD regions", "Validate replay routes"],
        last_updated=utc_now(),
    )