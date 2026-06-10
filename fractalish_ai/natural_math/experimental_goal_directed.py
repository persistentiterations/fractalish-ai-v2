"""
Natural Math v3.8 Experimental Goal Layer — NOT core.

Optional extensions: waypoints, target-gradient, trails, attractor bias, adaptation.
Canon trunk remains v3.6 core (v3_6_core.py).

Attractor bias is experimental. It is not part of the Natural Math core until it proves
it preserves locality, termination, and useful emergent behavior.
"""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExperimentalMetrics:
    mode: str
    success: bool
    steps: int
    revisits: int
    waypoint_hits: int
    energy_used: float
    trail_count: int
    node_count: int
    branch_count: int
    extend_count: int
    sense_count: int
    restrict_count: int
    trap_count: int
    target_gradient_helped: bool | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _neighbors(pos: tuple[int, int], w: int, h: int) -> list[tuple[int, int]]:
    x, y = pos
    opts = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [(nx, ny) for nx, ny in opts if 0 <= nx < w and 0 <= ny < h]


class ExperimentalGridRunner:
    """Grid runner for v3.8 experimental comparisons — separate from v3.6 core."""

    def __init__(
        self,
        *,
        seed: int = 7,
        grid_size: tuple[int, int] = (12, 12),
        start: tuple[int, int] = (1, 6),
        goal: tuple[int, int] = (10, 6),
        obstacles: set[tuple[int, int]] | None = None,
        waypoints: list[tuple[int, int]] | None = None,
        use_target_gradient: bool = False,
        use_trails: bool = False,
        lambda_attractor: float = 0.0,
        target_strength: float = 0.5,
        trail_deposit: float = 0.8,
        max_steps: int = 100,
        mode_name: str = "experimental",
    ) -> None:
        self.rng = random.Random(seed)
        self.w, self.h = grid_size
        self.start = start
        self.goal = goal
        self.obstacles = obstacles or set()
        self.waypoints = waypoints or [goal]
        self.use_target_gradient = use_target_gradient
        self.use_trails = use_trails
        self.lambda_attractor = lambda_attractor
        self.target_strength = target_strength
        self.trail_deposit = trail_deposit
        self.max_steps = max_steps
        self.mode_name = mode_name
        self.pos = start
        self.energy = 120.0
        self.visited: set[tuple[int, int]] = set()
        self.trails: dict[tuple[int, int], float] = {}
        self.waypoint_hits = 0
        self.revisits = 0
        self.traps = 0
        self.extend_count = 0
        self.sense_count = 0
        self.restrict_count = 0
        self.branch_count = 0

    def _attractor_pull(self, pos: tuple[int, int], target: tuple[int, int]) -> float:
        dx = target[0] - pos[0]
        dy = target[1] - pos[1]
        dist = max((dx * dx + dy * dy) ** 0.5, 1.0)
        return self.lambda_attractor / dist

    def _score(self, pos: tuple[int, int], target: tuple[int, int]) -> float:
        score = 0.0
        if self.use_target_gradient:
            dx = target[0] - pos[0]
            dy = target[1] - pos[1]
            score += self.target_strength * (dx + dy)
        if self.use_trails:
            score -= self.trails.get(pos, 0.0)
        if pos in self.visited:
            score -= 2.0
            self.traps += 1
        score += self._attractor_pull(pos, target)
        return score

    def step(self) -> bool:
        if self.pos == self.goal or self.energy <= 0:
            return False
        options = [n for n in _neighbors(self.pos, self.w, self.h) if n not in self.obstacles]
        if not options:
            self.restrict_count += 1
            self.energy -= 2.0
            return self.energy > 0

        target = self.waypoints[-1]
        if not self.use_target_gradient and not self.use_trails and self.lambda_attractor == 0:
            choice = self.rng.choice(options)
        else:
            scored = [(self._score(n, target), n) for n in options]
            scored.sort(key=lambda x: x[0], reverse=True)
            choice = scored[0][1]

        if self.pos in self.visited:
            self.revisits += 1
        self.visited.add(self.pos)
        if self.use_trails:
            self.trails[self.pos] = self.trails.get(self.pos, 0.0) + self.trail_deposit
            for k in list(self.trails):
                self.trails[k] *= 0.95
                if self.trails[k] < 0.01:
                    del self.trails[k]

        for wp in self.waypoints:
            if choice == wp:
                self.waypoint_hits += 1

        self.extend_count += 1
        self.energy -= 3.0
        self.pos = choice
        return self.pos != self.goal and self.energy > 0

    def run(self) -> ExperimentalMetrics:
        steps = 0
        while steps < self.max_steps and self.step():
            steps += 1
        success = self.pos == self.goal
        return ExperimentalMetrics(
            mode=self.mode_name,
            success=success,
            steps=steps,
            revisits=self.revisits,
            waypoint_hits=self.waypoint_hits,
            energy_used=round(120.0 - self.energy, 2),
            trail_count=len(self.trails),
            node_count=len(self.visited),
            branch_count=self.branch_count,
            extend_count=self.extend_count,
            sense_count=self.sense_count,
            restrict_count=self.restrict_count,
            trap_count=self.traps,
            notes="Experimental v3.8 goal layer — not core, not proof.",
        )


def run_mode_comparison(seed: int = 7) -> dict[str, Any]:
    obstacles = {(5, y) for y in range(3, 9)}
    common = dict(
        seed=seed,
        grid_size=(12, 12),
        start=(1, 6),
        goal=(10, 6),
        obstacles=obstacles,
        waypoints=[(4, 6), (7, 6), (10, 6)],
        max_steps=100,
    )
    modes = {
        "A_v3_6_core_baseline": ExperimentalGridRunner(**common, mode_name="A_v3_6_core_baseline"),
        "B_target_gradient": ExperimentalGridRunner(**common, use_target_gradient=True, mode_name="B_target_gradient"),
        "C_trail_memory": ExperimentalGridRunner(**common, use_trails=True, mode_name="C_trail_memory"),
        "D_target_plus_trail": ExperimentalGridRunner(
            **common, use_target_gradient=True, use_trails=True, mode_name="D_target_plus_trail"
        ),
        "E_weak_attractor_bias": ExperimentalGridRunner(
            **common, lambda_attractor=0.1, mode_name="E_weak_attractor_bias"
        ),
    }
    results = {k: r.run().to_dict() for k, r in modes.items()}
    core = results["A_v3_6_core_baseline"]
    tgt = results["B_target_gradient"]
    results["analysis"] = {
        "target_gradient_helped": tgt["success"] and not core["success"],
        "trail_helped": results["C_trail_memory"]["revisits"] < core["revisits"],
        "local_finite_energy_claim": "All modes use bounded local grid steps and finite energy budget.",
        "experimental_label": "Natural Math v3.8 Experimental Goal Layer — not core, not proof.",
    }
    return results