"""Demo: Experimental attractor bias (potential-field bias) — NOT core."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.natural_math.experimental_goal_directed import ExperimentalGridRunner

OUTPUT = ROOT / "outputs" / "natural_math_attractor_bias_summary.json"


def run_case(name: str, lambda_attractor: float, use_trails: bool = False) -> dict:
    runner = ExperimentalGridRunner(
        seed=7,
        grid_size=(12, 12),
        start=(1, 6),
        goal=(10, 6),
        obstacles={(5, y) for y in range(3, 9)},
        lambda_attractor=lambda_attractor,
        use_trails=use_trails,
        mode_name=name,
        max_steps=100,
    )
    m = runner.run()
    return m.to_dict()


def main() -> int:
    cases = {
        "A_no_attractor": run_case("A_no_attractor", 0.0),
        "B_weak_attractor": run_case("B_weak_attractor", 0.1),
        "C_strong_attractor": run_case("C_strong_attractor", 0.7),
        "D_attractor_plus_memory": run_case("D_attractor_plus_memory", 0.3, use_trails=True),
    }
    weak = cases["B_weak_attractor"]
    strong = cases["C_strong_attractor"]
    none = cases["A_no_attractor"]
    payload = {
        "label": "Experimental attractor bias (potential-field bias) — NOT Natural Math core.",
        "note": "Attractor bias is optional. It does not override EXTEND/SENSE/RESTRICT in v3.6 core.",
        "cases": cases,
        "analysis": {
            "weak_helped": weak["success"] and not none["success"],
            "strong_helped": strong["success"] and not none["success"],
            "strong_harmed": strong["trap_count"] > none["trap_count"] and not strong["success"],
            "efficiency_ranking": sorted(cases.keys(), key=lambda k: (-int(cases[k]["success"]), cases[k]["steps"])),
        },
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Natural Math — Experimental Attractor Bias Demo")
    print(payload["label"])
    for name, data in cases.items():
        print(f"  {name}: success={data['success']} steps={data['steps']} revisits={data['revisits']} traps={data['trap_count']}")
    print(f"Output: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())