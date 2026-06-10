"""Example wrapper for Cognitive Basin Simulation v1."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "experiments" / "cognitive_basin_sim_v1" / "run_simulation.py"


def main() -> int:
    print("Fractalish AI — Cognitive Basin Simulation v1")
    return subprocess.run([sys.executable, str(RUNNER)], cwd=str(ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())