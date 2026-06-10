"""Run Cognitive Basin Simulation v1."""

from __future__ import annotations

import sys
from pathlib import Path

SIM = Path(__file__).resolve().parent
ROOT = SIM.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.basin_sim import BasinSimulation
from fractalish_ai.basin_sim.scenarios import ALL_SCENARIOS

OUTPUT = SIM / "outputs"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    sim = BasinSimulation(output_dir=OUTPUT)
    results = sim.run_all_scenarios(ALL_SCENARIOS)
    sim.write_outputs(OUTPUT)
    summary = sim.build_summary()

    failed = sum(1 for r in results if not r.get("assertions_passed", True))

    print("Cognitive Basin Simulation v1")
    print("Stateful moving-basin simulation — not consciousness.")
    print("ReceptorEvent/PERCEPT → ATAL → RIGOR → CIRCUIT → FractalMemoryMap → GUARD → SERA → SessionGlyph")
    print()
    for r in results:
        status = "OK" if r.get("assertions_passed", True) else "FAIL"
        name = r.get("scenario_name", "?")
        guard = r.get("guard_decision", "?")
        print(f"[{status}] {name}: GUARD={guard}")
    print()
    print("=" * 60)
    print(f"Guard counts: {summary['guard_counts']}")
    print(f"Contradiction scars: {summary['contradiction_scars']}")
    print(f"HOLD/fog regions: {len(summary['hold_fog_regions'])}")
    print(f"Active attractors: {[a['node_id'] for a in summary['active_attractors'][:3]]}")
    print(f"Final SessionGlyph hash: {summary['final_session_glyph_hash']}")
    print(f"Output: {OUTPUT}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())