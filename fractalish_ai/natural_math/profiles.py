"""Natural Math runner profiles — smoke baseline and memory-enabled demos."""

from __future__ import annotations

from typing import Any


def smoke_profile() -> dict[str, Any]:
    """Memoryless baseline — efficiency trace only (not path-success demo)."""
    return {
        "name": "smoke",
        "memory_enabled": False,
        "comparison_mode": "efficiency_trace_only",
        "max_steps": 50,
        "seed": 7,
        "grid_size": (10, 10),
        "start": (1, 5),
        "goal": (8, 5),
        "obstacles": [(4, y) for y in range(2, 8)],
    }


def bifurcation_demo_profile() -> dict[str, Any]:
    """Memory-enabled grid demo — controlled solvable corridor."""
    return {
        "name": "bifurcation-demo",
        "memory_enabled": True,
        "comparison_mode": "controlled_path_success",
        "max_steps": 50,
        "seed": 7,
        "grid_size": (10, 10),
        "start": (1, 5),
        "goal": (8, 5),
        "obstacles": [(4, 2), (4, 7)],
        "p_bifurcate": 99,
        "trail_deposit": 0.5,
    }


def get_profile(name: str) -> dict[str, Any]:
    profiles = {
        "smoke": smoke_profile,
        "bifurcation-demo": bifurcation_demo_profile,
        "memory-enabled": bifurcation_demo_profile,
        "memoryless": smoke_profile,
    }
    if name not in profiles:
        raise ValueError(f"Unknown profile: {name}")
    return profiles[name]()