"""Run all Cognitive Basin Workbench scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(BENCH))

from scenarios import ALL_SCENARIOS
from workbench_report import (
    build_summary,
    write_scenario_output,
    write_summary,
)

OUTPUT = BENCH / "outputs"


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    print("Cognitive Basin Workbench")
    print("Traceable, stateful, ternary-gated cognition simulator — not consciousness.")
    print("PERCEPT → ATAL → RIGOR → CIRCUIT → GUARD → SERA → SessionGlyph")
    print()

    failed = 0
    for name, fn in ALL_SCENARIOS:
        result = fn()
        write_scenario_output(OUTPUT, result)
        results.append(result)
        assertions_ok = all(result.get("assertions", {}).values())
        if not assertions_ok:
            failed += 1
        status = "OK" if assertions_ok else "ASSERTION_FAIL"
        print(f"[{status}] {result['title']}")
        print(f"       GUARD={result['guard_decision']}")
        for line in result.get("narrative", [])[:2]:
            print(f"       {line}")
        print()

    summary = build_summary(results)
    json_path, md_path = write_summary(OUTPUT, summary)

    print("=" * 60)
    print("Workbench Summary")
    print(f"Scenarios: {len(results)}")
    print(f"Guard counts: {summary['guard_counts']}")
    print(f"Contradiction scars: {summary['contradiction_scars_created']}")
    print(f"Recovery routes: {summary['recovery_routes_created']}")
    print(f"Unresolved holds: {summary['unresolved_holds_carried_forward']}")
    print(f"Overclaims blocked: {summary['overclaims_blocked']}")
    print(f"Final SessionGlyph hash: {summary['final_session_glyph_hash']}")
    print(f"JSON: {json_path}")
    print(f"MD:   {md_path}")
    print()
    print("HOLD before false closure. Pressure is not truth. Similarity is not identity.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())