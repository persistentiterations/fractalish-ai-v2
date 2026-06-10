"""Cognitive Basin Simulation v1 tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.basin_sim import BasinSimulation
from fractalish_ai.basin_sim.scenarios import (
    ALL_SCENARIOS,
    scenario_contradiction_scar,
    scenario_false_closure_attempt,
    scenario_mcva_cannot_short_circuit,
    scenario_natural_math_process_trace,
    scenario_pressure_not_truth,
    scenario_recovery_after_interruption,
    scenario_similarity_not_identity,
)


def _fresh_sim() -> BasinSimulation:
    return BasinSimulation(activation_id="test-sim-001")


def test_sim_v1_runs_all_scenarios() -> None:
    sim = _fresh_sim()
    results = sim.run_all_scenarios(ALL_SCENARIOS)
    assert len(results) == 8
    assert all(r.get("assertions_passed", True) for r in results)


def test_false_closure_routes_to_hold() -> None:
    sim = _fresh_sim()
    result = scenario_false_closure_attempt(sim)
    assert result["guard_decision"] == "HOLD"
    assert result["assertions"]["false_continuity_detected"]


def test_contradiction_creates_scar_and_link() -> None:
    sim = _fresh_sim()
    result = scenario_contradiction_scar(sim)
    assert result["guard_decision"] == "HOLD"
    assert result["assertions"]["scar_written"]
    assert result["assertions"]["contradiction_link"]
    contra = [l for l in sim.fmm.links if l.relation_type == "contradiction"]
    assert len(contra) > 0


def test_pressure_does_not_create_truth_route() -> None:
    sim = _fresh_sim()
    result = scenario_pressure_not_truth(sim)
    assert result["guard_decision"] in ("HOLD", "WATCH")
    assert result["assertions"]["no_pressure_truth_route"]


def test_similarity_creates_analogy_not_identity() -> None:
    sim = _fresh_sim()
    result = scenario_similarity_not_identity(sim)
    assert result["guard_decision"] in ("WATCH", "HOLD")
    analogy = [l for l in sim.fmm.links if l.relation_type == "analogy"]
    assert len(analogy) > 0


def test_mcva_cannot_short_circuit_guard() -> None:
    sim = _fresh_sim()
    result = scenario_mcva_cannot_short_circuit(sim)
    assert result["assertions"]["mcva_positive"]
    assert result["guard_decision"] == "HOLD"


def test_natural_math_cautious_claim_allowed() -> None:
    sim = _fresh_sim()
    result = scenario_natural_math_process_trace(sim)
    assert result["cautious_guard"] in ("PROCEED", "WATCH")


def test_natural_math_overclaim_blocked() -> None:
    sim = _fresh_sim()
    result = scenario_natural_math_process_trace(sim)
    assert result["overclaim_guard"] == "HOLD"


def test_recovery_restores_open_loops() -> None:
    sim = _fresh_sim()
    for name, fn in ALL_SCENARIOS[:-1]:
        fn(sim)
    result = scenario_recovery_after_interruption(sim)
    assert result["assertions"]["purpose_recovered"]
    assert result["assertions"]["next_action_recovered"]


def test_final_session_glyph_has_hash() -> None:
    sim = _fresh_sim()
    sim.run_all_scenarios(ALL_SCENARIOS)
    summary = sim.build_summary()
    assert summary["final_session_glyph_hash"]
    assert len(summary["final_session_glyph_hash"]) >= 8