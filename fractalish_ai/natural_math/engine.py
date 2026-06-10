"""Natural Math v0.1 — simplified grid growth demo (stdlib only)."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any

EXTEND = "EXTEND"
SENSE = "SENSE"
RESTRICT = "RESTRICT"


@dataclass
class RunMetrics:
    success: bool
    total_steps: int
    revisits: int
    dead_ends: int
    branch_count: int
    extend_count: int
    sense_count: int
    restrict_count: int
    energy_spent: float
    efficiency_score: float
    memory_enabled: bool
    profile: str
    comparison_mode: str = "efficiency_trace_only"
    event_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _neighbors(pos: tuple[int, int], grid_size: tuple[int, int]) -> list[tuple[int, int]]:
    x, y = pos
    w, h = grid_size
    candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [(nx, ny) for nx, ny in candidates if 0 <= nx < w and 0 <= ny < h]


def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class GridGrowthSimulator:
    """Minimal local-process demo comparing memoryless vs trail-memory behavior."""

    def __init__(self, profile: dict[str, Any]) -> None:
        self.profile = profile
        self.rng = random.Random(profile.get("seed", 7))
        self.grid_size = tuple(profile["grid_size"])
        self.start = tuple(profile["start"])
        self.goal = tuple(profile["goal"])
        self.obstacles = set(tuple(o) for o in profile.get("obstacles", []))
        self.memory_enabled = bool(profile.get("memory_enabled", False))
        self.trail: dict[tuple[int, int], float] = {}
        self.visited: set[tuple[int, int]] = set()
        self.pos = self.start
        self.pressure = 0
        self.energy = 100.0
        self.event_log: list[dict[str, Any]] = []
        self.extend_count = 0
        self.sense_count = 0
        self.restrict_count = 0
        self.branch_count = 0
        self.revisits = 0
        self.dead_ends = 0
        self.energy_spent = 0.0
        self.tips: list[tuple[int, int]] = [self.start]

    def _is_blocked(self, pos: tuple[int, int]) -> bool:
        return pos in self.obstacles

    def _trail_value(self, pos: tuple[int, int]) -> float:
        return self.trail.get(pos, 0.0)

    def _choose_next(self, pos: tuple[int, int]) -> tuple[tuple[int, int] | None, str]:
        options = [n for n in _neighbors(pos, self.grid_size) if not self._is_blocked(n)]
        if not options:
            return None, RESTRICT

        if not self.memory_enabled:
            return self.rng.choice(options), EXTEND

        scored: list[tuple[float, tuple[int, int]]] = []
        for opt in options:
            trail_penalty = self._trail_value(opt) * 0.5
            goal_pull = -2.0 * _manhattan(opt, self.goal)
            revisit_penalty = -3.0 if opt in self.visited else 1.0
            score = goal_pull + revisit_penalty - trail_penalty
            scored.append((score, opt))
        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best = scored[0]
        if best_score < -1.5 and self.pressure >= self.profile.get("p_bifurcate", 5):
            self.branch_count += 1
            return best, EXTEND
        return best, EXTEND

    def step(self) -> bool:
        if self.pos == self.goal:
            return False

        action_pos, action = self._choose_next(self.pos)
        step_record: dict[str, Any] = {"step": len(self.event_log) + 1, "pos": self.pos, "action": action}

        if action == RESTRICT or action_pos is None:
            self.restrict_count += 1
            self.dead_ends += 1
            self.energy_spent += 2.0
            self.energy -= 2.0
            step_record["note"] = "dead_end"
            self.event_log.append(step_record)
            return self.energy > 0

        if action == SENSE:
            self.sense_count += 1
            self.energy_spent += 1.0
            self.energy -= 1.0
            self.pressure += 1
            step_record["note"] = "sense_at_pressure"
            self.event_log.append(step_record)
            return self.energy > 0

        if self.pos in self.visited:
            self.revisits += 1
        self.visited.add(self.pos)
        if self.memory_enabled:
            deposit = float(self.profile.get("trail_deposit", 0.5))
            self.trail[self.pos] = self.trail.get(self.pos, 0.0) + deposit
            for key in list(self.trail):
                self.trail[key] *= 0.95
                if self.trail[key] < 0.01:
                    del self.trail[key]

        self.extend_count += 1
        self.energy_spent += 3.0
        self.energy -= 3.0
        self.pos = action_pos
        step_record["next_pos"] = self.pos
        self.event_log.append(step_record)
        return self.energy > 0 and self.pos != self.goal

    def run(self) -> RunMetrics:
        steps = 0
        max_steps = int(self.profile.get("max_steps", 100))
        while steps < max_steps and self.step():
            steps += 1
        success = self.pos == self.goal
        novelty = len(self.visited)
        efficiency = (1.0 / max(self.energy_spent, 1.0)) * (10.0 if success else novelty / max(steps, 1))
        comparison_mode = self.profile.get("comparison_mode", "efficiency_trace_only")
        return RunMetrics(
            success=success,
            total_steps=steps,
            revisits=self.revisits,
            dead_ends=self.dead_ends,
            branch_count=self.branch_count,
            extend_count=self.extend_count,
            sense_count=self.sense_count,
            restrict_count=self.restrict_count,
            energy_spent=round(self.energy_spent, 2),
            efficiency_score=round(efficiency, 4),
            memory_enabled=self.memory_enabled,
            profile=self.profile.get("name", "unknown"),
            comparison_mode=comparison_mode,
            event_log=self.event_log,
        )


def compare_baseline_vs_memory(seed: int = 7) -> dict[str, Any]:
    from fractalish_ai.natural_math.profiles import bifurcation_demo_profile, smoke_profile

    baseline_profile = smoke_profile()
    baseline_profile["seed"] = seed
    memory_profile = bifurcation_demo_profile()
    memory_profile["seed"] = seed

    baseline = GridGrowthSimulator(baseline_profile).run()
    memory = GridGrowthSimulator(memory_profile).run()

    delta = memory.efficiency_score - baseline.efficiency_score
    return {
        "comparison_note": (
            "Baseline is efficiency_trace_only (memoryless random walk). "
            "Memory-enabled uses controlled_path_success corridor when solvable."
        ),
        "baseline": baseline.to_dict(),
        "memory_enabled": memory.to_dict(),
        "efficiency_delta": round(delta, 4),
        "revisit_delta": baseline.revisits - memory.revisits,
        "success_delta": int(memory.success) - int(baseline.success),
    }