"""Metrics aggregation for maze benchmark."""

from __future__ import annotations

import statistics
from typing import Any


def efficiency_score(success: bool, steps: int, revisits: int, energy_used: float) -> float:
    if not success:
        return round(max(0.0, 1.0 / max(steps, 1)) * (1.0 / (1.0 + revisits)), 4)
    base = 10.0 / max(steps, 1)
    revisit_penalty = 1.0 / (1.0 + revisits)
    energy_penalty = 1.0 / (1.0 + energy_used / 100.0)
    return round(base * revisit_penalty * energy_penalty, 4)


def aggregate_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for run in runs:
        key = (run["maze_name"], run["mode"])
        by_key.setdefault(key, []).append(run)

    aggregates: list[dict[str, Any]] = []
    for (maze_name, mode), group in sorted(by_key.items()):
        successes = [r for r in group if r["success"]]
        steps = [r["steps"] for r in group]
        revisits = [r["revisits"] for r in group]
        energy = [r["energy_used"] for r in group]
        efficiency = [r["efficiency_score"] for r in group]
        success_rate = len(successes) / len(group)
        failure_modes: dict[str, int] = {}
        for r in group:
            if not r["success"]:
                reason = r.get("failure_reason", "unknown")
                failure_modes[reason] = failure_modes.get(reason, 0) + 1

        aggregates.append(
            {
                "maze_name": maze_name,
                "mode": mode,
                "runs": len(group),
                "success_rate": round(success_rate, 4),
                "mean_steps": round(statistics.mean(steps), 2),
                "median_steps": round(statistics.median(steps), 2),
                "mean_revisits": round(statistics.mean(revisits), 2),
                "mean_energy_used": round(statistics.mean(energy), 2),
                "mean_efficiency_score": round(statistics.mean(efficiency), 4),
                "failure_modes": failure_modes,
            }
        )

    best_per_maze: dict[str, str] = {}
    for maze in {a["maze_name"] for a in aggregates}:
        maze_rows = [a for a in aggregates if a["maze_name"] == maze]
        best = max(maze_rows, key=lambda r: (r["success_rate"], r["mean_efficiency_score"], -r["mean_steps"]))
        best_per_maze[maze] = best["mode"]

    memory_modes = {"memory_enabled", "attractor_plus_memory", "trail_stigmergy"}
    attractor_modes = {"attractor_bias", "attractor_plus_memory"}

    def _compare(mode_set: set[str], baseline: str, metric: str) -> dict[str, Any]:
        helped: list[str] = []
        harmed: list[str] = []
        for maze in best_per_maze:
            base = next((a for a in aggregates if a["maze_name"] == maze and a["mode"] == baseline), None)
            if not base:
                continue
            for mode in mode_set:
                row = next((a for a in aggregates if a["maze_name"] == maze and a["mode"] == mode), None)
                if not row:
                    continue
                if row["success_rate"] > base["success_rate"] or (
                    row["success_rate"] == base["success_rate"] and row["mean_efficiency_score"] > base["mean_efficiency_score"]
                ):
                    helped.append(f"{maze}:{mode}")
                elif row["success_rate"] < base["success_rate"] or row["mean_steps"] > base["mean_steps"] * 1.5:
                    harmed.append(f"{maze}:{mode}")
        return {"helped": helped, "harmed": harmed, "metric": metric}

    return {
        "aggregate_by_maze_mode": aggregates,
        "best_mode_per_maze": best_per_maze,
        "memory_vs_memoryless": _compare(memory_modes, "memoryless", "success_and_efficiency"),
        "attractor_bias_analysis": _compare(attractor_modes, "memoryless", "success_and_trap_sensitivity"),
    }