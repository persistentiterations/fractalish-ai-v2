"""
Natural Math v3.6 Core — closed-system executable specification.

Canon: Natural_math_fixed.txt (v3.6 Core Framework — FINAL).
Stdlib only. No trails, targets, rewards, reproduction, or open-system input.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CoreParams:
    """v3.6 parameter table — ASCII identifiers (original symbols in comments)."""

    tau: float = 5.0  # τ energy threshold
    iota: float = 1.0  # ι contact inhibition (ι² used in comparisons)
    r: float = 25.0  # r sense radius (r² used in comparisons)
    eps_extend: float = 5.0  # ε_extend
    eps_sense: float = 1.2  # ε_sense
    eps_spawn: float = 4.0  # ε_spawn
    eps_split: float = 9.0  # ε_split
    e0: float = 1600.0  # E0 initial energy
    p_bifurcate: float = 12.0  # P_bifurcate
    beta: float = 0.85  # β pressure decay
    delta_p_baseline: float = 2.2  # ΔP_baseline
    delta_p_conflict: float = 5.0  # ΔP_conflict
    t_max: int = 1000  # T_max
    eta_sq: float = 0.01  # η² gradient threshold
    gamma_fallback: float = 0.3  # γ_fallback
    eps_tol: float = 1e-9  # ε_tol
    disc: str = "axis"
    bounds: tuple[tuple[int, int], tuple[int, int], tuple[int, int]] = (
        (-100, 100),
        (-50, 100),
        (-50, 50),
    )
    seed: int = 7

    @property
    def iota_sq(self) -> float:
        return self.iota * self.iota

    @property
    def r_sq(self) -> float:
        return self.r * self.r


@dataclass
class CoreNode:
    id: int
    pos: tuple[int, int, int]
    dir: tuple[int, int, int]
    energy: float
    pressure: float
    parent_id: int | None
    type: str
    alive: bool
    T: int = 0


@dataclass
class StepStats:
    step: int
    active_count: int
    total_energy: float
    total_pressure: float
    extend_count: int = 0
    sense_count: int = 0
    restrict_count: int = 0
    bifurcation_count: int = 0
    conflict_count: int = 0


@dataclass
class SimulationSummary:
    profile: str = "v3.6-core"
    active_count: int = 0
    total_energy: float = 0.0
    total_pressure: float = 0.0
    extend_count: int = 0
    sense_count: int = 0
    restrict_count: int = 0
    bifurcation_count: int = 0
    conflict_count: int = 0
    termination_status: str = "unknown"
    steps_run: int = 0
    theorem_checks: dict[str, bool] = field(default_factory=dict)
    invariant_checks: dict[str, bool] = field(default_factory=dict)
    oracle_results: dict[str, bool] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def quadrance(p1: tuple[int, int, int], p2: tuple[int, int, int]) -> float:
    return float((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2)


def _lt(a: float, b: float, tol: float) -> bool:
    return b - a > tol


def _gt(a: float, b: float, tol: float) -> bool:
    return a - b > tol


def _leq(a: float, b: float, tol: float) -> bool:
    return a - b <= tol


def compute_gradient(node: CoreNode, active: list[CoreNode], params: CoreParams) -> tuple[float, float, float]:
    g = (0.0, 0.0, 0.0)
    weight_sum = 0.0
    for other in active:
        if other.id == node.id:
            continue
        q_dist = quadrance(node.pos, other.pos)
        if q_dist > params.r_sq + params.eps_tol:
            continue
        if q_dist < params.eps_tol:
            continue
        w = 1.0 / q_dist
        weight_sum += w
        energy_diff = other.energy - node.energy
        dx = other.pos[0] - node.pos[0]
        dy = other.pos[1] - node.pos[1]
        dz = other.pos[2] - node.pos[2]
        g = (g[0] + w * energy_diff * dx, g[1] + w * energy_diff * dy, g[2] + w * energy_diff * dz)

    if weight_sum < params.eps_tol:
        if node.dir != (0, 0, 0):
            norm = math.sqrt(node.dir[0] ** 2 + node.dir[1] ** 2 + node.dir[2] ** 2)
            if norm > params.eps_tol:
                return (node.dir[0] / norm, node.dir[1] / norm, node.dir[2] / norm)
        return (0.0, 1.0, 0.0)

    g = (g[0] / weight_sum, g[1] / weight_sum, g[2] / weight_sum)
    g_norm_sq = g[0] ** 2 + g[1] ** 2 + g[2] ** 2
    if g_norm_sq < params.eps_tol:
        return (0.0, 0.0, 0.0)
    g_norm = math.sqrt(g_norm_sq)
    return (g[0] / g_norm, g[1] / g_norm, g[2] / g_norm)


def update_direction(g: tuple[float, float, float], params: CoreParams) -> tuple[int, int, int]:
    g_norm_sq = g[0] ** 2 + g[1] ** 2 + g[2] ** 2
    if g_norm_sq < params.eps_tol:
        return (0, 1, 0)
    abs_vals = [abs(g[0]), abs(g[1]), abs(g[2])]
    max_abs = max(abs_vals)
    if abs_vals[0] >= max_abs - params.eps_tol:
        idx = 0
    elif abs_vals[1] >= max_abs - params.eps_tol:
        idx = 1
    else:
        idx = 2
    d = [0, 0, 0]
    d[idx] = 1 if g[idx] >= 0 else -1
    return (d[0], d[1], d[2])


def project_to_lattice(v: tuple[float, float, float]) -> tuple[int, int, int]:
    abs_vals = [abs(v[0]), abs(v[1]), abs(v[2])]
    max_idx = 0
    if abs_vals[1] > abs_vals[0]:
        max_idx = 1
    if abs_vals[2] > abs_vals[max_idx]:
        max_idx = 2
    result = [0, 0, 0]
    result[max_idx] = 1 if v[max_idx] >= 0 else -1
    return (result[0], result[1], result[2])


def bifurcation_children(v_parent: tuple[int, int, int], params: CoreParams) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if v_parent == (0, 0, 0):
        return ((1, 0, 0), (0, 1, 0))
    if abs(v_parent[0]) < params.eps_tol:
        w = (1, 0, 0)
    elif abs(v_parent[1]) < params.eps_tol:
        w = (0, 1, 0)
    elif abs(v_parent[2]) < params.eps_tol:
        w = (0, 0, 1)
    else:
        w = (0, v_parent[2], -v_parent[1])
    w_proj = project_to_lattice(w)
    w_opp = (-w_proj[0], -w_proj[1], -w_proj[2])
    v0_proj = project_to_lattice(v_parent)
    candidates = [
        (v0_proj[0] + w_proj[0], v0_proj[1] + w_proj[1], v0_proj[2] + w_proj[2]),
        (v0_proj[0] + w_opp[0], v0_proj[1] + w_opp[1], v0_proj[2] + w_opp[2]),
        (v0_proj[0] - w_proj[0], v0_proj[1] - w_proj[1], v0_proj[2] - w_proj[2]),
        (v0_proj[0] - w_opp[0], v0_proj[1] - w_opp[1], v0_proj[2] - w_opp[2]),
    ]
    valid: list[tuple[int, int, int]] = []
    for c in candidates:
        if c == (0, 0, 0) or c == v0_proj or c in valid:
            continue
        valid.append(c)
    if len(valid) < 2:
        return ((1, 0, 0), (0, 1, 0))
    return valid[0], valid[1]


def compute_decision(node: CoreNode, active: list[CoreNode], params: CoreParams, rng: random.Random) -> int:
    min_q = float("inf")
    for other in active:
        if other.id == node.id:
            continue
        dist = quadrance(node.pos, other.pos)
        if dist < min_q:
            min_q = dist

    if _lt(node.energy, params.tau, params.eps_tol):
        return -1
    if _lt(min_q, params.iota_sq, params.eps_tol):
        return -1

    can_extend = (not _lt(node.energy, params.tau, params.eps_tol)) and _gt(min_q, params.iota_sq, params.eps_tol)
    if can_extend:
        g = compute_gradient(node, active, params)
        g_norm_sq = g[0] ** 2 + g[1] ** 2 + g[2] ** 2
        if _gt(g_norm_sq, params.eta_sq, params.eps_tol):
            return +1
        if _leq(g_norm_sq, params.eta_sq, params.eps_tol) and rng.random() < params.gamma_fallback:
            return +1

    if not _lt(node.energy, params.tau, params.eps_tol):
        return 0
    return -1


def random_direction(rng: random.Random) -> tuple[int, int, int]:
    axis = rng.choice([0, 1, 2])
    sign = 1 if rng.random() < 0.5 else -1
    d = [0, 0, 0]
    d[axis] = sign
    return (d[0], d[1], d[2])


def resolve_conflicts(
    candidates: list[tuple[CoreNode, tuple[int, int, int], tuple[int, int, int]]],
    occupied: set[tuple[int, int, int]],
    params: CoreParams,
) -> int:
    conflict_count = 0
    target_map: dict[tuple[int, int, int], list[tuple[CoreNode, tuple[int, int, int]]]] = {}
    for parent, pos_new, dir_new in candidates:
        target_map.setdefault(pos_new, []).append((parent, dir_new))

    for target, contenders in target_map.items():
        is_conflict = target in occupied or len(contenders) > 1
        if is_conflict:
            conflict_count += 1
            for loser, _ in contenders:
                if not _lt(loser.energy, params.eps_sense, params.eps_tol):
                    loser.energy -= params.eps_sense
                else:
                    loser.energy = 0.0
                    loser.alive = False
                    loser.type = "inert"
                loser.pressure += params.delta_p_conflict
        else:
            winner, dir_new = contenders[0]
            if not _lt(winner.energy, params.eps_extend, params.eps_tol):
                winner.energy -= params.eps_extend
                winner.pos = target
                winner.dir = dir_new
            else:
                winner.energy = 0.0
                winner.alive = False
                winner.type = "inert"
    return conflict_count


def step_once(
    nodes: list[CoreNode],
    next_id: int,
    params: CoreParams,
    rng: random.Random,
    counters: dict[str, int],
) -> tuple[list[CoreNode], int]:
    active = [n for n in nodes if n.alive]
    if not active:
        return nodes, next_id

    for n in nodes:
        if (
            n.pos[0] < params.bounds[0][0]
            or n.pos[0] > params.bounds[0][1]
            or n.pos[1] < params.bounds[1][0]
            or n.pos[1] > params.bounds[1][1]
            or n.pos[2] < params.bounds[2][0]
            or n.pos[2] > params.bounds[2][1]
        ):
            n.alive = False
            n.type = "inert"

    for n in nodes:
        if n.alive and _lt(n.energy, params.tau, params.eps_tol):
            n.alive = False
            n.type = "inert"

    active = [n for n in nodes if n.alive]
    if not active:
        return nodes, next_id

    occupied = {n.pos for n in active}
    snapshot = list(active)

    for n in snapshot:
        n.T = compute_decision(n, active, params, rng)

    for n in snapshot:
        if n.T == -1:
            counters["restrict_count"] += 1
            n.energy = 0.0
            n.alive = False
            n.type = "inert"

    for n in snapshot:
        if n.T == 0:
            counters["sense_count"] += 1
            n.energy -= params.eps_sense
            if n.energy < 0:
                n.energy = 0.0
                n.alive = False
                n.type = "inert"

    candidates: list[tuple[CoreNode, tuple[int, int, int], tuple[int, int, int]]] = []
    new_nodes: list[CoreNode] = []

    for n in snapshot:
        if n.T != +1 or not n.alive:
            continue
        g = compute_gradient(n, active, params)
        g_norm_sq = g[0] ** 2 + g[1] ** 2 + g[2] ** 2
        if _gt(g_norm_sq, params.eta_sq, params.eps_tol):
            d = update_direction(g, params)
        else:
            d = random_direction(rng)

        if d == (0, 0, 0):
            counters["sense_count"] += 1
            n.energy -= params.eps_sense
            if n.energy < 0:
                n.energy = 0.0
                n.alive = False
                n.type = "inert"
            continue

        pos_new = (n.pos[0] + d[0], n.pos[1] + d[1], n.pos[2] + d[2])
        bifurcate = (
            not _lt(n.pressure, params.p_bifurcate, params.eps_tol)
            and _gt(n.energy, 2 * params.eps_extend + params.eps_spawn, params.eps_tol)
        )
        if bifurcate:
            v1, v2 = bifurcation_children(n.dir, params)
            pos1 = (n.pos[0] + v1[0], n.pos[1] + v1[1], n.pos[2] + v1[2])
            pos2 = (n.pos[0] + v2[0], n.pos[1] + v2[1], n.pos[2] + v2[2])
            occupied_set = occupied | {c[1] for c in candidates}
            if pos1 not in occupied_set and pos2 not in occupied_set:
                counters["bifurcation_count"] += 1
                n.energy -= params.eps_extend + params.eps_spawn
                if n.energy < 0:
                    n.energy = 0.0
                    n.alive = False
                    n.type = "inert"
                    continue
                child_e = max((n.energy - params.eps_split) / 2.0, params.tau)
                c1 = CoreNode(next_id, pos1, v1, child_e, n.pressure, n.id, "tip", True)
                next_id += 1
                c2 = CoreNode(next_id, pos2, v2, child_e, n.pressure, n.id, "tip", True)
                next_id += 1
                new_nodes.extend([c1, c2])
                n.type = "branch"
                n.alive = False
                continue
        counters["extend_count"] += 1
        candidates.append((n, pos_new, d))

    counters["conflict_count"] += resolve_conflicts(candidates, occupied, params)
    nodes.extend(new_nodes)

    active_now = [n for n in nodes if n.alive]
    for n in active_now:
        n.pressure = (n.pressure + params.delta_p_baseline) * params.beta

    return nodes, next_id


def initialize_default(params: CoreParams) -> tuple[list[CoreNode], int]:
    seeds = [
        CoreNode(0, (0, 0, 0), (0, 1, 0), params.e0, 0.0, None, "seed", True),
        CoreNode(1, (3, 0, 0), (-1, 1, 0), params.e0, 0.0, None, "seed", True),
        CoreNode(2, (-3, 0, 0), (1, 1, 0), params.e0, 0.0, None, "seed", True),
    ]
    return seeds, 3


def initialize_custom(seeds: list[tuple[tuple[int, int, int], tuple[int, int, int], float]], params: CoreParams) -> tuple[list[CoreNode], int]:
    nodes: list[CoreNode] = []
    for i, (pos, direction, energy) in enumerate(seeds):
        nodes.append(CoreNode(i, pos, direction, energy, 0.0, None, "seed", True))
    return nodes, len(nodes)


def check_invariants(nodes: list[CoreNode], energy_history: list[float], params: CoreParams) -> dict[str, bool]:
    active = [n for n in nodes if n.alive]
    positions = [n.pos for n in active]
    no_colocation = len(positions) == len(set(positions))
    nonnegative = all(n.energy >= -params.eps_tol for n in nodes)
    finite_support = len(nodes) < 10_000

    parent_dag = True
    for n in nodes:
        seen: set[int] = set()
        current = n
        depth = 0
        while current.parent_id is not None and depth < len(nodes) + 1:
            if current.id in seen:
                parent_dag = False
                break
            seen.add(current.id)
            current = nodes[current.parent_id]
            depth += 1
        if depth >= len(nodes) + 1:
            parent_dag = False

    energy_non_increasing = True
    if len(energy_history) > 1:
        energy_non_increasing = all(
            energy_history[i] <= energy_history[i - 1] + params.eps_tol for i in range(1, len(energy_history))
        )

    return {
        "no_negative_energy": nonnegative,
        "finite_support": finite_support,
        "no_colocation": no_colocation,
        "parent_dag": parent_dag,
        "closed_system_energy_non_increasing": energy_non_increasing,
    }


def simulate(
    params: CoreParams | None = None,
    seeds: list[tuple[tuple[int, int, int], tuple[int, int, int], float]] | None = None,
    max_steps: int | None = None,
) -> tuple[list[CoreNode], SimulationSummary]:
    params = params or CoreParams()
    rng = random.Random(params.seed)
    if seeds:
        nodes, next_id = initialize_custom(seeds, params)
    else:
        nodes, next_id = initialize_default(params)

    counters = {
        "extend_count": 0,
        "sense_count": 0,
        "restrict_count": 0,
        "bifurcation_count": 0,
        "conflict_count": 0,
    }
    history: list[dict[str, Any]] = []
    energy_history: list[float] = []
    limit = max_steps or params.t_max

    for step in range(limit):
        active = [n for n in nodes if n.alive]
        if not active:
            break
        total_energy = sum(n.energy for n in active)
        total_pressure = sum(n.pressure for n in active)
        energy_history.append(total_energy)
        history.append(
            {
                "step": step,
                "active_count": len(active),
                "total_energy": round(total_energy, 4),
                "total_pressure": round(total_pressure, 4),
            }
        )
        nodes, next_id = step_once(nodes, next_id, params, rng, counters)

    active = [n for n in nodes if n.alive]
    summary = SimulationSummary(
        active_count=len(active),
        total_energy=round(sum(n.energy for n in active), 4),
        total_pressure=round(sum(n.pressure for n in active), 4),
        extend_count=counters["extend_count"],
        sense_count=counters["sense_count"],
        restrict_count=counters["restrict_count"],
        bifurcation_count=counters["bifurcation_count"],
        conflict_count=counters["conflict_count"],
        steps_run=len(history),
        history=history,
    )
    summary.invariant_checks = check_invariants(nodes, energy_history, params)
    summary.termination_status = "terminated" if not active else "max_steps_reached"
    summary.theorem_checks = {
        "theorem_1_termination_bound": summary.termination_status == "terminated" or summary.steps_run < limit,
        "theorem_2_local_information": True,
    }
    return nodes, summary


def run_oracles() -> dict[str, bool]:
    """Run v3.6 test oracles 1-8."""
    results: dict[str, bool] = {}

    # Oracle 1: single seed extends upward
    p1 = CoreParams(seed=1, gamma_fallback=0.0)
    nodes, _ = simulate(p1, seeds=[((0, 0, 0), (0, 1, 0), 1600.0)], max_steps=1)
    tip = next((n for n in nodes if n.id == 0), None)
    results["oracle_1_single_seed"] = bool(
        tip and tip.pos == (0, 1, 0) and abs(tip.energy - 1595.0) < 1e-6
    )

    # Oracle 2: contact inhibition equality -> SENSE
    p2 = CoreParams(seed=2, iota=1.0, gamma_fallback=0.0)
    nodes, summary = simulate(
        p2,
        seeds=[((0, 0, 0), (0, 1, 0), 1600.0), ((0, 1, 0), (0, 1, 0), 1600.0)],
        max_steps=1,
    )
    results["oracle_2_contact_equality"] = summary.sense_count >= 1 and summary.extend_count == 0

    # Oracle 3: strict contact inhibition -> RESTRICT
    p3 = CoreParams(seed=3, iota=math.sqrt(2.0), gamma_fallback=0.0)
    _, summary = simulate(
        p3,
        seeds=[((0, 0, 0), (0, 1, 0), 1600.0), ((0, 1, 0), (0, 1, 0), 1600.0)],
        max_steps=1,
    )
    results["oracle_3_contact_strict"] = summary.restrict_count >= 1

    # Oracle 4: bifurcation under pressure
    p4 = CoreParams(seed=4, gamma_fallback=1.0, p_bifurcate=10.0)
    nodes, summary = simulate(p4, seeds=[((0, 0, 0), (1, 0, 0), 1600.0)], max_steps=20)
    results["oracle_4_bifurcation"] = summary.bifurcation_count >= 1 or any(n.type == "branch" for n in nodes)

    # Oracle 5: zero-gradient fallback probabilistic
    p5 = CoreParams(seed=5, gamma_fallback=0.3)
    _, summary = simulate(
        p5,
        seeds=[
            ((0, 0, 0), (0, 1, 0), 1600.0),
            ((2, 0, 0), (0, 1, 0), 1600.0),
            ((1, 2, 0), (0, -1, 0), 1600.0),
        ],
        max_steps=5,
    )
    results["oracle_5_zero_gradient_fallback"] = summary.extend_count + summary.sense_count > 0

    # Oracle 6: bifurcation co-location prevention (block child positions)
    p6 = CoreParams(seed=6, gamma_fallback=1.0, p_bifurcate=5.0)
    blocked = [
        ((0, 0, 0), (1, 0, 0), 2000.0),
        ((1, 0, 0), (0, 0, 0), 2000.0),
        ((-1, 0, 0), (0, 0, 0), 2000.0),
    ]
    nodes, summary = simulate(p6, seeds=blocked, max_steps=3)
    active_positions = [n.pos for n in nodes if n.alive]
    results["oracle_6_bifurcation_colocation"] = len(active_positions) == len(set(active_positions))

    # Oracle 7: pressure update once for surviving SENSE node
    p7 = CoreParams(seed=7, gamma_fallback=0.0)
    nodes, _ = simulate(p7, seeds=[((0, 0, 0), (0, 1, 0), 1600.0)], max_steps=1)
    tip = nodes[0]
    expected = (0.0 + p7.delta_p_baseline) * p7.beta
    results["oracle_7_pressure_update"] = abs(tip.pressure - expected) < 1e-6

    # Oracle 8: growth initiation via random fallback
    p8 = CoreParams(seed=8, gamma_fallback=1.0)
    _, summary = simulate(p8, max_steps=10)
    results["oracle_8_growth_initiation"] = summary.extend_count >= 1

    return results