"""Demo: Natural Math v3.8 Experimental Goal Layer (not core)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.natural_math.experimental_goal_directed import run_mode_comparison

OUTPUT = ROOT / "outputs" / "natural_math_goal_directed_v3_8_summary.json"


def main() -> int:
    results = run_mode_comparison()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("Natural Math v3.8 Experimental Goal Layer")
    print("NOT core. NOT proof. NOT merged into trunk.")
    print()
    for mode, data in results.items():
        if mode == "analysis":
            continue
        print(f"{mode}: success={data['success']} steps={data['steps']} revisits={data['revisits']} waypoint_hits={data['waypoint_hits']}")
    print()
    print("Analysis:", results["analysis"])
    print(f"Output: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())