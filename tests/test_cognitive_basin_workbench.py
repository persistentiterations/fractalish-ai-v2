"""Cognitive Basin Workbench tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "experiments" / "cognitive_basin_workbench"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from scenarios import (
    scenario_contradiction_scar,
    scenario_false_continuity,
    scenario_overclaim_block,
    scenario_pressure_not_truth,
    scenario_recovery_route,
    scenario_similarity_not_identity,
)


def test_workbench_false_continuity_holds() -> None:
    result = scenario_false_continuity()
    assert result["guard_decision"] == "HOLD"
    assert result["assertions"]["false_closure_prevented"]


def test_workbench_contradiction_scar_holds() -> None:
    result = scenario_contradiction_scar()
    assert result["guard_decision"] == "HOLD"
    assert result["assertions"]["scar_written"]


def test_workbench_recovery_route_recovers_purpose() -> None:
    result = scenario_recovery_route()
    assert result["assertions"]["purpose_recovered"]
    assert result["assertions"]["next_action_recovered"]


def test_workbench_overclaim_blocked() -> None:
    result = scenario_overclaim_block()
    assert result["assertions"]["all_overclaims_blocked"]
    assert result["guard_decision"] in ("HOLD", "REVERSE")


def test_workbench_pressure_not_truth() -> None:
    result = scenario_pressure_not_truth()
    assert result["guard_decision"] in ("HOLD", "WATCH")
    assert result["assertions"]["pressure_not_truth"]


def test_workbench_similarity_not_identity() -> None:
    result = scenario_similarity_not_identity()
    assert result["assertions"]["similarity_warning_issued"]
    assert result["guard_decision"] in ("WATCH", "HOLD")