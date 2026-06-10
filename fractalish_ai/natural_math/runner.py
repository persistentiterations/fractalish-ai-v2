"""Natural Math runner CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fractalish_ai.natural_math.engine import GridGrowthSimulator, compare_baseline_vs_memory
from fractalish_ai.natural_math.profiles import get_profile


def run_profile(profile_name: str, out_dir: str | Path | None = None) -> dict[str, Any]:
    profile = get_profile(profile_name)
    result = GridGrowthSimulator(profile).run().to_dict()
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "natural_math_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def run_comparison(out_dir: str | Path | None = None, seed: int = 7) -> dict[str, Any]:
    comparison = compare_baseline_vs_memory(seed=seed)
    if out_dir:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "natural_math_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    return comparison