"""RIGOR analyzer tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.rigor import run_rigor_checks


def test_rigor_detects_missing_source() -> None:
    findings = run_rigor_checks({"claim": "Something happened.", "source": ""})
    source = next(f for f in findings if f.analyzer == "source_presence")
    assert source.state == "HOLD"


def test_rigor_detects_contradiction() -> None:
    findings = run_rigor_checks({
        "source": "merge@local",
        "claim": "Conflicting reports.",
        "contradictions": [
            {"source": "a@local", "claim": "Up"},
            {"source": "b@local", "claim": "Down"},
        ],
    })
    contradiction = next(f for f in findings if f.analyzer == "contradiction")
    assert contradiction.state == "HOLD"