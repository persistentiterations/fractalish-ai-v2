"""Demo: Natural Math v3.6 core — closed-system specification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.natural_math.v3_6_core import run_oracles, simulate, CoreParams

OUTPUT = ROOT / "outputs" / "natural_math_v3_6_core_summary.json"


def main() -> int:
    params = CoreParams(seed=7)
    _, summary = simulate(params, max_steps=200)
    oracle_results = run_oracles()
    summary.oracle_results = oracle_results

    payload = summary.to_dict()
    payload["note"] = (
        "Natural Math v3.6 Core — closed system. "
        "No trails, targets, rewards, or open-system input. "
        "Canon: Natural_math_fixed.txt."
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Fractalish AI — Natural Math v3.6 Core Demo")
    print(f"Active count: {summary.active_count}")
    print(f"Total energy: {summary.total_energy}")
    print(f"EXTEND={summary.extend_count} SENSE={summary.sense_count} RESTRICT={summary.restrict_count}")
    print(f"Bifurcations={summary.bifurcation_count} Conflicts={summary.conflict_count}")
    print(f"Termination: {summary.termination_status}")
    print("Invariants:", summary.invariant_checks)
    passed = sum(1 for v in oracle_results.values() if v)
    print(f"Oracles: {passed}/{len(oracle_results)} passed")
    print(f"Output: {OUTPUT}")
    return 0 if passed == len(oracle_results) else 1


if __name__ == "__main__":
    raise SystemExit(main())