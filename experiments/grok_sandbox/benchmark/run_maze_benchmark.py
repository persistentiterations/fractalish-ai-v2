"""Run full maze benchmark across modes, mazes, and seeds."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SANDBOX = Path(__file__).resolve().parents[1]
MAZE_DIR = SANDBOX / "maze"
sys.path.insert(0, str(MAZE_DIR))

from maze_examples import list_maze_names  # noqa: E402
from maze_metrics import aggregate_runs  # noqa: E402
from maze_runner import MODE_LABELS, run_maze, save_run  # noqa: E402

OUTPUT_DIR = SANDBOX / "outputs"
SEEDS = list(range(1, 26))  # 25 seeds
MODES = [
    "memoryless",
    "memory_enabled",
    "v3_6_core_local",
    "attractor_bias",
    "attractor_plus_memory",
    "trail_stigmergy",
]
PRIMARY_MAZES = ["easy_corridor", "branching_dead_ends", "trap_heavy"]
OPTIONAL_MAZES = ["open_field_island", "spiral"]


def _interpretation(agg: dict) -> dict[str, str]:
    mem = agg.get("memory_vs_memoryless", {})
    att = agg.get("attractor_bias_analysis", {})
    lines = {
        "memory": (
            "Memory reduced revisits in several runs; success gains depend on maze layout. "
            f"Helped: {len(mem.get('helped', []))} cases; harmed: {len(mem.get('harmed', []))} cases."
        ),
        "attractor_bias": (
            "Attractor-bias uses experimental goal-field (nonlocal goal knowledge). "
            f"Helped: {len(att.get('helped', []))} cases; harmed: {len(att.get('harmed', []))} cases. "
            "May help easy corridors but can trap in trap-heavy mazes."
        ),
        "v3_6_core": "v3.6 core mode uses local neighbor sensing only — no global goal coordinates.",
        "disclaimer": (
            "Maze-running is a controlled benchmark for local decision-making, memory, revisits, "
            "traps, and constraint navigation. It is not a claim of general intelligence."
        ),
    }
    return lines


def write_csv(path: Path, aggregates: list[dict]) -> None:
    if not aggregates:
        return
    fields = list(aggregates[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in aggregates:
            writer.writerow({k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in row.items()})


def write_md(path: Path, summary: dict) -> None:
    agg = summary["aggregate_by_maze_mode"]
    lines = [
        "# Maze Benchmark Summary",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        summary["interpretation"]["disclaimer"],
        "",
        "## Aggregate Results",
        "",
        "| Maze | Mode | Success Rate | Mean Steps | Mean Revisits | Mean Efficiency |",
        "|------|------|--------------|------------|-----------------|-----------------|",
    ]
    for row in agg:
        lines.append(
            f"| {row['maze_name']} | {row['mode']} | {row['success_rate']:.0%} | "
            f"{row['mean_steps']} | {row['mean_revisits']} | {row['mean_efficiency_score']} |"
        )
    lines.extend(["", "## Best mode per maze", ""])
    for maze, mode in summary["best_mode_per_maze"].items():
        lines.append(f"- **{maze}**: `{mode}`")
    lines.extend(["", "## Interpretation", ""])
    for key, text in summary["interpretation"].items():
        if key != "disclaimer":
            lines.append(f"- **{key}**: {text}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mazes = PRIMARY_MAZES + OPTIONAL_MAZES
    all_runs = []

    print("Grok Sandbox — Maze Benchmark")
    print(f"Mazes: {len(mazes)} | Modes: {len(MODES)} | Seeds: {len(SEEDS)}")
    total = len(mazes) * len(MODES) * len(SEEDS)
    done = 0

    for maze_name in mazes:
        for mode in MODES:
            for seed in SEEDS:
                result = run_maze(maze_name, mode, seed=seed)
                save_run(result)
                all_runs.append(result.to_dict())
                done += 1
                if done % 50 == 0:
                    print(f"  {done}/{total} runs complete...")

    agg = aggregate_runs(all_runs)
    interpretation = _interpretation(agg)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mazes": mazes,
        "modes": {m: MODE_LABELS[m] for m in MODES},
        "seeds": SEEDS,
        "total_runs": len(all_runs),
        "aggregate_by_maze_mode": agg["aggregate_by_maze_mode"],
        "best_mode_per_maze": agg["best_mode_per_maze"],
        "memory_vs_memoryless": agg["memory_vs_memoryless"],
        "attractor_bias_analysis": agg["attractor_bias_analysis"],
        "interpretation": interpretation,
        "sample_runs": all_runs[:6],
    }

    json_path = OUTPUT_DIR / "maze_benchmark_summary.json"
    csv_path = OUTPUT_DIR / "maze_benchmark_summary.csv"
    md_path = OUTPUT_DIR / "maze_benchmark_summary.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_csv(csv_path, agg["aggregate_by_maze_mode"])
    write_md(md_path, summary)

    # Sandbox report for merge decision
    best_row = max(agg["aggregate_by_maze_mode"], key=lambda r: (r["success_rate"], r["mean_efficiency_score"]))
    worst_row = min(agg["aggregate_by_maze_mode"], key=lambda r: (r["success_rate"], -r["mean_steps"]))
    report = {
        "what_was_built": "Local ASCII maze benchmark comparing 6 decision modes across 5 mazes and 25 seeds.",
        "how_to_run": [
            "python experiments/grok_sandbox/benchmark/run_maze_benchmark.py",
            "python experiments/grok_sandbox/maze/maze_runner.py",
            "cd experiments/grok_sandbox/dashboard && python -m http.server 8000",
        ],
        "strongest_result": best_row,
        "weakest_result": worst_row,
        "memory_helped": interpretation["memory"],
        "attractor_bias": interpretation["attractor_bias"],
        "merge_recommendation": "partial_merge",
        "merge_notes": (
            "Partially merge: maze benchmark harness and v3.6-local mode reporting into trunk examples; "
            "keep attractor/trail modes in experiments/ only."
        ),
        "benchmark_summary_path": str(json_path),
    }
    (OUTPUT_DIR / "grok_sandbox_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "grok_sandbox_report.md").write_text(
        "\n".join(
            [
                "# Grok Sandbox Report",
                "",
                "## What was built",
                report["what_was_built"],
                "",
                "## How to run",
                *[f"- `{c}`" for c in report["how_to_run"]],
                "",
                "## Strongest result",
                f"- {best_row['maze_name']} / {best_row['mode']}: success_rate={best_row['success_rate']}",
                "",
                "## Weakest result",
                f"- {worst_row['maze_name']} / {worst_row['mode']}: success_rate={worst_row['success_rate']}",
                "",
                "## Merge recommendation",
                f"**{report['merge_recommendation']}** — {report['merge_notes']}",
                "",
                interpretation["disclaimer"],
            ]
        ),
        encoding="utf-8",
    )

    print(f"\nBenchmark complete: {len(all_runs)} runs")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    print(f"MD:   {md_path}")
    print(f"Report: {OUTPUT_DIR / 'grok_sandbox_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())