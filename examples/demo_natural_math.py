"""Demo: memoryless baseline vs memory-enabled Natural Math."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fractalish_ai.natural_math.runner import run_comparison

OUTPUT = ROOT / "outputs" / "demo_natural_math"


def main() -> int:
    comparison = run_comparison(OUTPUT)
    print("Fractalish AI — Natural Math Comparison")
    print(comparison.get("comparison_note", ""))
    print()
    b = comparison["baseline"]
    m = comparison["memory_enabled"]
    print(f"Baseline mode: {b.get('comparison_mode', 'efficiency_trace_only')}")
    print(f"Memory mode:   {m.get('comparison_mode', 'controlled_path_success')}")
    print()
    print("Memoryless baseline:")
    print(f"  success={b['success']} steps={b['total_steps']} revisits={b['revisits']} efficiency={b['efficiency_score']}")
    print(f"  EXTEND={b['extend_count']} SENSE={b['sense_count']} RESTRICT={b['restrict_count']} branches={b['branch_count']}")
    print()
    print("Memory-enabled Natural Math:")
    print(f"  success={m['success']} steps={m['total_steps']} revisits={m['revisits']} efficiency={m['efficiency_score']}")
    print(f"  EXTEND={m['extend_count']} SENSE={m['sense_count']} RESTRICT={m['restrict_count']} branches={m['branch_count']}")
    print()
    print(f"Efficiency delta (memory - baseline): {comparison['efficiency_delta']}")
    print(f"Output: {OUTPUT / 'natural_math_comparison.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())