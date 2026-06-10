"""SessionGlyph recovery tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractalish_ai.core_runtime import default_basin_state, run_activation_event
from fractalish_ai.session_glyph import SessionGlyph, basin_from_glyph, build_session_glyph


def test_recovery_route_from_session_glyph() -> None:
    basin = default_basin_state()
    basin["purpose"] = "recovery test purpose"
    basin["operator_constraints"] = ["test_constraint"]

    record = run_activation_event({
        "source": "operator@local",
        "claim": "Open analysis step.",
        "evidence": ["step1"],
        "supported": True,
        "speculation": True,
        "purpose": basin["purpose"],
    }, basin)

    glyph_dict = record["updated_session_glyph"]
    recovered = basin_from_glyph(glyph_dict)

    assert recovered["purpose"] == "recovery test purpose"
    assert recovered["operator_constraints"] == ["test_constraint"]
    assert recovered["circuit"]["open_loops"] == glyph_dict["open_loops"]
    assert glyph_dict["next_action"]

    glyph = SessionGlyph(**{k: glyph_dict[k] for k in SessionGlyph.__dataclass_fields__})
    assert glyph.state_hash == glyph_dict["state_hash"]