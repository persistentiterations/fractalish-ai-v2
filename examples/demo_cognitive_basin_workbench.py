"""Example wrapper for Cognitive Basin Workbench."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "experiments" / "cognitive_basin_workbench" / "run_workbench.py"


def main() -> int:
    print("Fractalish AI — Cognitive Basin Workbench Demo")
    print(f"Runner: {RUNNER}")
    result = subprocess.run([sys.executable, str(RUNNER)], cwd=str(ROOT))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())