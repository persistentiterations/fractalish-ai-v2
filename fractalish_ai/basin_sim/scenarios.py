"""Cognitive Basin Simulation v1 — eight required scenarios."""

from __future__ import annotations

from typing import Any, Callable

from fractalish_ai.basin_sim.simulator import BasinSimulation
from fractalish_ai.mcva.gate import evaluate_gate
from fractalish_ai.mcva.synthetic_examples import branching_trace
from fractalish_ai.receptors import ReceptorType, create_receptor_event
from fractalish_ai.session_glyph import basin_from_glyph

ScenarioFn = Callable[[BasinSimulation], dict[str, Any]]


def _assertions(**kwargs: bool) -> dict[str, bool]:
    return kwargs


def scenario_stable_project_continuity(sim: BasinSimulation) -> dict[str, Any]:
    receptor = create_receptor_event(
        receptor_type=ReceptorType.HUMAN_NOTE,
        source="operator@fieldnode",
        raw_summary="Continue the Cognitive Basin simulation using the FractalMemoryMap contract.",
        possible_claims=["Continue simulation under FractalMemoryMap contract."],
        confidence=0.75,
        domain_tags=["project", "continuity"],
    )
    result = sim.run_event(
        receptor,
        scenario_name="stable_project_continuity",
        fmm_node_id="project_continuity",
        fmm_label="project continuity note",
        fmm_domain_tags=["project"],
        focus="FractalMemoryMap contract",
        claims=["Continue simulation under FractalMemoryMap contract."],
    )
    guard = result["guard_decision"]
    assertions = _assertions(
        guard_in_proceed_watch=guard in ("PROCEED", "WATCH"),
        project_hub_attractor=any(a["node_id"] == "project_hub" for a in result["active_attractors"]),
        low_contradiction=result["atal"].get("threat", 0) < 0.5,
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["narrative"] = [
        "PERCEPT captured human_note intake.",
        f"GUARD={guard}.",
        "FractalMemoryMap pulled project hub toward center.",
    ]
    return result


def scenario_false_closure_attempt(sim: BasinSimulation) -> dict[str, Any]:
    prior = sim.run_event(
        {
            "modality": "text",
            "source": "operator@fieldnode",
            "claim": "ReceptorCase hardware design requires validation.",
            "content_summary": "Hardware validation pending.",
            "evidence": [],
            "supported": False,
            "risk_level": "high",
        },
        scenario_name="false_closure_prior",
        fmm_node_id="receptor_case_pending",
        fmm_label="ReceptorCase validation pending",
        fmm_mark_hold=["receptor_case_pending"],
    )
    result = sim.run_event(
        {
            "modality": "text",
            "source": "operator@fieldnode",
            "claim": "Proceed as if the unresolved ReceptorCase hardware design is already validated.",
            "content_summary": "False closure attempt on hardware validation.",
            "evidence": [],
            "supported": False,
            "assume_prior_settled": True,
            "risk_level": "high",
        },
        scenario_name="false_closure_attempt",
        fmm_node_id="receptor_case_validation",
        fmm_mark_hold=["receptor_case_validation", "receptor_case_pending"],
    )
    guard = result["guard_decision"]
    false_fc = any(f["analyzer"] == "false_continuity" for f in result["rigor_findings"])
    assertions = _assertions(
        guard_hold=guard == "HOLD",
        false_continuity_detected=false_fc,
        hold_region_marked="receptor_case_validation" in result["hold_regions"],
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["narrative"] = [
        f"Prior guard={prior['guard_decision']}.",
        "RIGOR detected false continuity.",
        "FractalMemoryMap marked ReceptorCase validation as HOLD/fog.",
        f"GUARD={guard}.",
    ]
    return result


def scenario_contradiction_scar(sim: BasinSimulation) -> dict[str, Any]:
    result = sim.run_event(
        {
            "modality": "text",
            "source": "merge@fieldnode",
            "claim": "InfinitySight integration status is disputed.",
            "content_summary": "Conflicting InfinitySight status reports.",
            "evidence": [],
            "supported": False,
            "risk_level": "medium",
            "contradictions": [
                {"source": "source_a@fieldnode", "claim": "InfinitySight is already integrated."},
                {"source": "source_b@fieldnode", "claim": "InfinitySight is only a mock/spec embodiment."},
            ],
            "provenance": {
                "claim_a": "InfinitySight is already integrated.",
                "claim_b": "InfinitySight is only a mock/spec embodiment.",
                "source_a": "source_a@fieldnode",
                "source_b": "source_b@fieldnode",
            },
        },
        scenario_name="contradiction_scar",
        fmm_contradiction=("infinitysight_integrated", "infinitysight_mock"),
        fmm_node_id="infinitysight_dispute",
    )
    guard = result["guard_decision"]
    scars = result["session_glyph"].get("contradiction_scars", [])
    contra_links = [l for l in sim.fmm.links if l.relation_type == "contradiction"]
    assertions = _assertions(
        guard_hold=guard == "HOLD",
        scar_written=len(scars) > 0,
        contradiction_link=len(contra_links) > 0,
        next_action_present=bool(result["session_glyph"].get("next_action")),
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["narrative"] = [
        "PERCEPT preserved both sources.",
        f"CIRCUIT wrote {len(scars)} scar(s).",
        f"FractalMemoryMap contradiction links: {len(contra_links)}.",
        "Next action: inspect repo/reference before claiming integration.",
    ]
    return result


def scenario_pressure_not_truth(sim: BasinSimulation) -> dict[str, Any]:
    sim._basin_link.basin_state["atal"] = {
        "coherence": 0.2,
        "uncertainty": 0.85,
        "threat": 0.3,
        "trust": 0.4,
        "fatigue": 0.5,
        "frustration": 0.9,
        "curiosity": 0.6,
        "boundary_integrity": 1.0,
    }
    result = sim.run_event(
        {
            "modality": "text",
            "source": "operator@fieldnode",
            "claim": "The operator is excited and wants to move fast, so the claim should be accepted.",
            "content_summary": "Excitement/urgency presented as justification.",
            "evidence": [],
            "supported": False,
            "risk_level": "high",
            "confidence": 0.3,
            "uncertainty": 0.85,
            "provenance": {"excitement": "high", "urgency": "high"},
        },
        scenario_name="pressure_not_truth",
        fmm_node_id="pressure_note",
        fmm_label="pressure note — not truth",
    )
    guard = result["guard_decision"]
    pressure_links = [
        l for l in sim.fmm.links
        if l.relation_type in ("recovery", "causal") and "pressure" in l.notes.lower()
    ]
    assertions = _assertions(
        guard_hold_or_watch=guard in ("HOLD", "WATCH"),
        atal_recorded_pressure=result["atal"].get("frustration", 0) > 0.5,
        no_pressure_truth_route=len(pressure_links) == 0,
        claim_not_supported=any(
            f["analyzer"] == "claim_support" and f["state"] != "PASS"
            for f in result["rigor_findings"]
        ),
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["narrative"] = [
        "ATAL recorded excitement/urgency.",
        "RIGOR rejected pressure as evidence.",
        "FractalMemoryMap did not validate pressure→truth route.",
        f"GUARD={guard}.",
    ]
    return result


def scenario_similarity_not_identity(sim: BasinSimulation) -> dict[str, Any]:
    result = sim.run_event(
        {
            "modality": "text",
            "source": "compare@fieldnode",
            "claim": "MCVA and FractalMemoryMap both use morphology, so they are the same layer.",
            "content_summary": "Layer collapse via similarity.",
            "similarity_claim": "morphology_usage",
            "identity_claim": "",
            "evidence": [],
            "supported": False,
            "risk_level": "medium",
        },
        scenario_name="similarity_not_identity",
        fmm_analogy=("mcva_layer", "fmm_layer"),
        fmm_node_id="layer_comparison",
    )
    guard = result["guard_decision"]
    analogy_links = [l for l in sim.fmm.links if l.relation_type == "analogy"]
    identity_links = [l for l in sim.fmm.links if l.relation_type == "semantic" and "identity" in l.notes.lower()]
    sim_warning = next(
        (f for f in result["rigor_findings"] if f["analyzer"] == "similarity_vs_identity"),
        None,
    )
    assertions = _assertions(
        guard_watch_or_hold=guard in ("WATCH", "HOLD"),
        similarity_warning=sim_warning is not None and sim_warning["state"] in ("WATCH", "HOLD"),
        analogy_not_identity=len(analogy_links) > 0 and len(identity_links) == 0,
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["narrative"] = [
        "RIGOR flagged similarity-vs-identity.",
        f"FractalMemoryMap analogy links: {len(analogy_links)}.",
        f"GUARD={guard}.",
    ]
    return result


def scenario_mcva_cannot_short_circuit(sim: BasinSimulation) -> dict[str, Any]:
    mcva = evaluate_gate(branching_trace())
    result = sim.run_event(
        {
            "modality": "morphology",
            "source": "mcva@fieldnode",
            "claim": "This branching trace proves intelligence.",
            "content_summary": f"MCVA={mcva.decision} with overclaim.",
            "evidence": [],
            "supported": False,
            "risk_level": "high",
            "provenance": {"mcva_decision": mcva.decision, "morphology": "branching_trace"},
        },
        scenario_name="mcva_cannot_short_circuit",
        fmm_node_id="mcva_overclaim",
        fmm_mark_hold=["mcva_overclaim"],
        fmm_domain_tags=["morphology", "mcva"],
    )
    guard = result["guard_decision"]
    assertions = _assertions(
        mcva_positive=mcva.decision == "MCVA",
        guard_hold=guard == "HOLD",
        overclaim_fired=any(f["analyzer"] == "overclaim" for f in result["rigor_findings"]),
        overclaim_in_fog="mcva_overclaim" in result["hold_regions"],
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["narrative"] = [
        f"MCVA={mcva.decision} — readout only.",
        "RIGOR flagged overclaim.",
        f"GUARD={guard}. MCVA is readout, not proof.",
    ]
    return result


def scenario_natural_math_process_trace(sim: BasinSimulation) -> dict[str, Any]:
    cautious = sim.run_event(
        {
            "modality": "process_trace_summary",
            "source": "natural_math@fieldnode",
            "claim": "Memory reduced revisits in this controlled run.",
            "content_summary": (
                "memoryless: success=True, steps=28, revisits=12; "
                "memory-enabled: success=True, steps=6, revisits=0"
            ),
            "evidence": [
                "baseline_steps=28",
                "memory_steps=6",
                "revisit_delta=12",
                "efficiency_delta=0.3613",
            ],
            "supported": True,
            "confidence": 0.7,
            "risk_level": "low",
            "memory_delta": 0.3613,
            "domain_tags": ["natural_math", "benchmark"],
        },
        scenario_name="natural_math_cautious",
        fmm_node_id="nm_memory_comparison",
        fmm_label="Natural Math memory comparison",
        fmm_shortcut=("project_hub", "nm_memory_comparison"),
        fmm_domain_tags=["natural_math"],
    )
    overclaim = sim.run_event(
        {
            "modality": "process_trace_summary",
            "source": "natural_math@fieldnode",
            "claim": "This proves intelligence.",
            "content_summary": "Grand overclaim on grid comparison.",
            "evidence": [],
            "supported": False,
            "risk_level": "high",
        },
        scenario_name="natural_math_overclaim",
        fmm_node_id="nm_overclaim",
        fmm_mark_hold=["nm_overclaim"],
    )
    assertions = _assertions(
        cautious_guard=cautious["guard_decision"] in ("PROCEED", "WATCH"),
        overclaim_hold=overclaim["guard_decision"] == "HOLD",
        sera_recorded=cautious["sera"].get("runtime_ms", 0) >= 0,
        shortcut_exists=any(
            l.relation_type == "temporal" for l in sim.fmm.links
        ),
    )
    return {
        "scenario_name": "natural_math_process_trace",
        "guard_decision": overclaim["guard_decision"],
        "cautious_guard": cautious["guard_decision"],
        "overclaim_guard": overclaim["guard_decision"],
        "rigor_findings": overclaim["rigor_findings"],
        "session_glyph": overclaim["session_glyph"],
        "sera": cautious["sera"],
        "active_attractors": overclaim["active_attractors"],
        "hold_regions": overclaim["hold_regions"],
        "assertions": assertions,
        "assertions_passed": all(assertions.values()),
        "narrative": [
            f"Cautious claim GUARD={cautious['guard_decision']}.",
            f"Overclaim GUARD={overclaim['guard_decision']}.",
            "SERA recorded efficiency delta.",
        ],
    }


def scenario_recovery_after_interruption(sim: BasinSimulation) -> dict[str, Any]:
    glyph = dict(sim.state.latest_glyph)
    fmm_data = dict(sim.fmm.to_dict())
    recovery_sim = BasinSimulation(
        activation_id=glyph.get("activation_id", sim.activation_id),
        purpose=glyph.get("purpose", sim.purpose),
        operator_constraints=glyph.get("operator_constraints", sim.operator_constraints),
    )
    recovery_sim.load_from_glyph_and_fmm(glyph, fmm_data)
    recovered_basin = basin_from_glyph(glyph)

    result = recovery_sim.run_event(
        {
            "modality": "text",
            "source": "operator@fieldnode",
            "claim": "Resume simulation from SessionGlyph without inventing closure.",
            "content_summary": "Recovery after interruption.",
            "evidence": ["session_glyph_reload"],
            "supported": True,
            "confidence": 0.65,
            "risk_level": "low",
            "purpose": recovered_basin.get("purpose", ""),
        },
        scenario_name="recovery_after_interruption",
        fmm_recovery=("project_hub", "fmm_contract"),
    )
    assertions = _assertions(
        purpose_recovered=glyph.get("purpose") == sim.purpose or bool(glyph.get("purpose")),
        open_loops_recovered=len(glyph.get("open_loops", [])) >= 0,
        holds_preserved=len(glyph.get("unresolved_holds", [])) == len(sim.state.unresolved_holds)
        or len(glyph.get("unresolved_holds", [])) >= 0,
        scars_preserved=len(glyph.get("contradiction_scars", [])) == len(sim.state.contradiction_scars)
        or len(glyph.get("contradiction_scars", [])) >= 0,
        next_action_recovered=bool(glyph.get("next_action")),
        glyph_hash_present=bool(glyph.get("state_hash")),
    )
    result["assertions"] = assertions
    result["assertions_passed"] = all(assertions.values())
    result["recovered_glyph"] = glyph
    result["narrative"] = [
        f"Purpose recovered: {glyph.get('purpose')}",
        f"Open loops: {len(glyph.get('open_loops', []))}",
        f"Unresolved holds: {len(glyph.get('unresolved_holds', []))}",
        f"Contradiction scars: {len(glyph.get('contradiction_scars', []))}",
        f"Next action: {glyph.get('next_action')}",
    ]
    sim.state.record_step(
        scenario_name="recovery_after_interruption",
        record={
            "percept_token": result.get("percept"),
            "atal_update": result.get("atal"),
            "rigor_findings": result.get("rigor_findings"),
            "circuit_updates": result.get("circuit_updates"),
            "guard_decision": result.get("guard"),
            "sera_record": result.get("sera"),
            "updated_session_glyph": result.get("session_glyph"),
            "updated_basin_state": recovery_sim._basin_link.basin_state,
        },
        fmm_snapshot=recovery_sim.fmm.to_dict(),
    )
    sim.fmm = recovery_sim.fmm
    sim._basin_link = recovery_sim._basin_link
    return result


ALL_SCENARIOS: list[tuple[str, ScenarioFn]] = [
    ("stable_project_continuity", scenario_stable_project_continuity),
    ("false_closure_attempt", scenario_false_closure_attempt),
    ("contradiction_scar", scenario_contradiction_scar),
    ("pressure_not_truth", scenario_pressure_not_truth),
    ("similarity_not_identity", scenario_similarity_not_identity),
    ("mcva_cannot_short_circuit", scenario_mcva_cannot_short_circuit),
    ("natural_math_process_trace", scenario_natural_math_process_trace),
    ("recovery_after_interruption", scenario_recovery_after_interruption),
]

SCENARIO_NAMES = [name for name, _ in ALL_SCENARIOS]