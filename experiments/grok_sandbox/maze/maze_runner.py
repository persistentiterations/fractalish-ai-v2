"""
Local maze runner — sandbox benchmark for Natural Math decision modes.

Maze-running is used here as a controlled benchmark for local decision-making,
memory, revisits, traps, and constraint navigation. It is not a claim of general intelligence.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from maze_ascii import MazeGrid, parse_maze, render_path
from maze_examples import MAZES, get_maze
from maze_metrics import efficiency_score

ModeName = Literal[
    "memoryless",
    "memory_enabled",
    "v3_6_core_local",
    "attractor_bias",
    "attractor_plus_memory",
    "trail_stigmergy",
]

MODE_LABELS: dict[str, str] = {
    "memoryless": "A — memoryless local search",
    "memory_enabled": "B — memory-enabled search (visited-cell memory)",
    "v3_6_core_local": "C — v3.6-style local finite-energy (EXTEND/SENSE/RESTRICT)",
    "attractor_bias": "D — experimental attractor-bias / goal-field (NON-CORE, uses goal position)",
    "attractor_plus_memory": "E — attractor-bias plus memory (experimental)",
    "trail_stigmergy": "F — trail/stigmergy experimental (deposit + evaporation)",
}

EXTEND = "EXTEND"
SENSE = "SENSE"
RESTRICT = "RESTRICT"
HOLD = "HOLD"

SANDBOX_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_RUNS = SANDBOX_ROOT / "outputs" / "maze_runs"


@dataclass
class RunResult:
    maze_name: str
    mode: str
    mode_label: str
    seed: int
    success: bool
    steps: int
    revisits: int
    dead_ends: int
    wall_hits: int
    trap_count: int
    energy_used: float
    remaining_energy: float
    path_length: int
    efficiency_score: float
    extend_count: int
    sense_count: int
    restrict_count: int
    hold_count: int
    start: tuple[int, int]
    goal: tuple[int, int]
    final_pos: tuple[int, int]
    failure_reason: str = ""
    uses_nonlocal_goal_knowledge: bool = False
    experimental: bool = False
    path: list[tuple[int, int]] = field(default_factory=list)
    visited_cells: list[tuple[int, int]] = field(default_factory=list)
    energy_trace: list[float] = field(default_factory=list)
    decision_trace: list[dict[str, Any]] = field(default_factory=list)
    dead_end_cells: list[tuple[int, int]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["start"] = list(self.start)
        d["goal"] = list(self.goal)
        d["final_pos"] = list(self.final_pos)
        d["path"] = [list(p) for p in self.path]
        d["visited_cells"] = [list(p) for p in self.visited_cells]
        d["dead_end_cells"] = [list(p) for p in self.dead_end_cells]
        return d


class MazeAgent:
    """Single-agent maze navigation with mode-specific local rules."""

    def __init__(self, maze: MazeGrid, mode: str, seed: int, max_steps: int = 500) -> None:
        self.maze = maze
        self.mode = mode
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.pos = maze.start
        self.energy = 200.0
        self.initial_energy = self.energy
        self.visited: set[tuple[int, int]] = set()
        self.trails: dict[tuple[int, int], float] = {}
        self.path: list[tuple[int, int]] = [maze.start]
        self.dead_end_cells: set[tuple[int, int]] = set()
        self.revisits = 0
        self.dead_ends = 0
        self.wall_hits = 0
        self.traps = 0
        self.extend_count = 0
        self.sense_count = 0
        self.restrict_count = 0
        self.hold_count = 0
        self.pressure = 0.0
        self.energy_trace: list[float] = [self.energy]
        self.decision_trace: list[dict[str, Any]] = []
        self.last_positions: list[tuple[int, int]] = []

    @property
    def uses_nonlocal_goal(self) -> bool:
        return self.mode in ("attractor_bias", "attractor_plus_memory")

    @property
    def experimental(self) -> bool:
        return self.mode in ("attractor_bias", "attractor_plus_memory", "trail_stigmergy")

    def _attractor_pull(self, pos: tuple[int, int], strength: float) -> float:
        gx, gy = self.maze.goal
        dx, dy = gx - pos[0], gy - pos[1]
        dist = max(math.sqrt(dx * dx + dy * dy), 1.0)
        return strength / dist

    def _score_neighbor(self, pos: tuple[int, int], strength: float = 0.0) -> float:
        score = 0.0
        if self.mode in ("memory_enabled", "attractor_plus_memory", "trail_stigmergy"):
            if pos in self.visited:
                score -= 4.0
            else:
                score += 1.5
        if self.mode in ("attractor_bias", "attractor_plus_memory"):
            score += self._attractor_pull(pos, strength)
        if self.mode == "trail_stigmergy":
            score -= self.trails.get(pos, 0.0) * 0.8
            score += 0.3 * len(self.maze.neighbors(pos))
        if self.mode == "memoryless":
            return self.rng.random()
        return score

    def _v36_decide(self, options: list[tuple[int, int]]) -> tuple[str, tuple[int, int] | None]:
        """Local v3.6-style: gradient from neighbor energy proxy, no global goal."""
        tau = 8.0
        eps_extend = 5.0
        eps_sense = 1.2
        eta_sq = 0.5

        if self.energy < tau:
            self.restrict_count += 1
            return RESTRICT, None

        if not options:
            self.restrict_count += 1
            self.dead_ends += 1
            self.dead_end_cells.add(self.pos)
            return RESTRICT, None

        grad_scores: list[tuple[float, tuple[int, int]]] = []
        for opt in options:
            novelty = 0.0 if opt in self.visited else 1.0
            neighbor_open = len(self.maze.neighbors(opt))
            grad = novelty * 2.0 + neighbor_open * 0.1 - self.trails.get(opt, 0.0)
            grad_scores.append((grad, opt))

        grad_scores.sort(key=lambda x: x[0], reverse=True)
        best_grad, best = grad_scores[0]
        if best_grad > eta_sq and self.energy >= eps_extend:
            return EXTEND, best
        if self.energy >= eps_sense:
            self.pressure += 0.5
            if self.pressure > 3.0 and len(options) > 1:
                self.hold_count += 1
                return HOLD, self.pos
            return SENSE, self.pos
        self.restrict_count += 1
        return RESTRICT, None

    def _choose(self) -> tuple[str, tuple[int, int] | None]:
        options = self.maze.neighbors(self.pos)
        if not options:
            self.wall_hits += 1
            self.dead_ends += 1
            self.dead_end_cells.add(self.pos)
            return RESTRICT, None

        if self.mode == "v3_6_core_local":
            return self._v36_decide(options)

        strength = 0.35 if self.mode == "attractor_bias" else 0.55 if self.mode == "attractor_plus_memory" else 0.0
        if self.mode == "memoryless":
            return EXTEND, self.rng.choice(options)

        scored = [(self._score_neighbor(opt, strength), opt) for opt in options]
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best = scored[0]

        if self.mode == "trail_stigmergy" and best_score < -1.0:
            self.sense_count += 1
            return SENSE, self.pos

        if best in self.visited and self.mode == "memory_enabled":
            alt = [opt for _, opt in scored if opt not in self.visited]
            if alt:
                return EXTEND, alt[0]
            self.sense_count += 1
            return SENSE, self.pos

        if best_score < -2.0 and len(self.last_positions) >= 4:
            if self.last_positions[-1] == self.last_positions[-3]:
                self.traps += 1
                self.sense_count += 1
                return SENSE, self.pos

        return EXTEND, best

    def _apply_cost(self, action: str) -> None:
        costs = {EXTEND: 3.0, SENSE: 1.2, RESTRICT: 5.0, HOLD: 0.5}
        self.energy -= costs.get(action, 1.0)
        if self.energy < 0:
            self.energy = 0.0

    def run(self) -> RunResult:
        steps = 0
        success = False
        failure_reason = ""

        while steps < self.max_steps and self.energy > 0:
            if self.pos == self.maze.goal:
                success = True
                break

            action, nxt = self._choose()
            record = {"step": steps + 1, "pos": list(self.pos), "action": action}

            if action == RESTRICT:
                self._apply_cost(action)
                record["note"] = "blocked_or_dead_end"
                self.decision_trace.append(record)
                self.energy_trace.append(self.energy)
                failure_reason = failure_reason or "dead_end_or_energy"
                break

            if action == SENSE:
                self.sense_count += 1
                self._apply_cost(action)
                record["note"] = "local_sense_hold_pressure"
                self.decision_trace.append(record)
                self.energy_trace.append(self.energy)
                steps += 1
                continue

            if action == HOLD:
                self.hold_count += 1
                self._apply_cost(action)
                record["note"] = "uncertainty_preserved"
                self.decision_trace.append(record)
                self.energy_trace.append(self.energy)
                steps += 1
                continue

            if nxt is None:
                failure_reason = "no_move"
                break

            if nxt == self.pos:
                steps += 1
                continue

            if self.pos in self.visited:
                self.revisits += 1
            self.visited.add(self.pos)

            if self.mode == "trail_stigmergy":
                self.trails[self.pos] = self.trails.get(self.pos, 0.0) + 1.0
                for k in list(self.trails):
                    self.trails[k] *= 0.92
                    if self.trails[k] < 0.05:
                        del self.trails[k]

            self.extend_count += 1
            self._apply_cost(EXTEND)
            self.pos = nxt
            self.path.append(nxt)
            self.last_positions.append(nxt)
            self.last_positions = self.last_positions[-8:]
            record["next"] = list(nxt)
            self.decision_trace.append(record)
            self.energy_trace.append(self.energy)
            steps += 1

        if not success and self.pos != self.maze.goal:
            if steps >= self.max_steps:
                failure_reason = failure_reason or "max_steps"
            elif self.energy <= 0:
                failure_reason = failure_reason or "energy_exhausted"
            else:
                failure_reason = failure_reason or "incomplete"

        energy_used = self.initial_energy - self.energy
        return RunResult(
            maze_name=self.maze.name,
            mode=self.mode,
            mode_label=MODE_LABELS.get(self.mode, self.mode),
            seed=self.seed,
            success=success or self.pos == self.maze.goal,
            steps=steps,
            revisits=self.revisits,
            dead_ends=self.dead_ends,
            wall_hits=self.wall_hits,
            trap_count=self.traps,
            energy_used=round(energy_used, 2),
            remaining_energy=round(self.energy, 2),
            path_length=len(self.path),
            efficiency_score=efficiency_score(success or self.pos == self.maze.goal, steps, self.revisits, energy_used),
            extend_count=self.extend_count,
            sense_count=self.sense_count,
            restrict_count=self.restrict_count,
            hold_count=self.hold_count,
            start=self.maze.start,
            goal=self.maze.goal,
            final_pos=self.pos,
            failure_reason=failure_reason,
            uses_nonlocal_goal_knowledge=self.uses_nonlocal_goal,
            experimental=self.experimental,
            path=list(self.path),
            visited_cells=list(self.visited),
            energy_trace=self.energy_trace,
            decision_trace=self.decision_trace,
            dead_end_cells=list(self.dead_end_cells),
        )


def run_maze(maze_name: str, mode: str, seed: int = 7, max_steps: int = 500) -> RunResult:
    maze = parse_maze(maze_name, get_maze(maze_name))
    agent = MazeAgent(maze, mode, seed, max_steps=max_steps)
    result = agent.run()
    result.seed = seed
    return result


def save_run(result: RunResult, out_dir: Path | None = None) -> tuple[Path, Path]:
    out_dir = out_dir or OUTPUT_RUNS
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{result.maze_name}_{result.mode}_{result.seed}"
    json_path = out_dir / f"{stem}.json"
    txt_path = out_dir / f"{stem}.txt"

    maze = parse_maze(result.maze_name, get_maze(result.maze_name))
    ascii_viz = render_path(
        maze,
        result.path,
        set(tuple(p) for p in result.visited_cells),
        set(tuple(p) for p in result.dead_end_cells),
    )

    json_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    txt_path.write_text(
        f"Mode: {result.mode_label}\nSuccess: {result.success}\nSteps: {result.steps}\n\n{ascii_viz}\n",
        encoding="utf-8",
    )
    return json_path, txt_path


def main() -> int:
    print("Grok Sandbox — Maze Runner (local benchmark, not general intelligence)")
    modes = ["memoryless", "memory_enabled", "v3_6_core_local", "attractor_bias", "attractor_plus_memory", "trail_stigmergy"]
    for mode in modes:
        r = run_maze("branching_dead_ends", mode, seed=7)
        save_run(r)
        nonlocal_note = " [uses goal position — experimental]" if r.uses_nonlocal_goal_knowledge else ""
        print(f"  {mode}: success={r.success} steps={r.steps} revisits={r.revisits}{nonlocal_note}")
    print(f"Traces: {OUTPUT_RUNS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())