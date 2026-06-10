"""SERA — cost, waste, and efficiency metrics."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class SeraRecord:
    runtime_ms: float = 0.0
    input_size: int = 0
    output_size: int = 0
    hold_count: int = 0
    reverse_count: int = 0
    unsupported_claim_count: int = 0
    source_missing_count: int = 0
    contradiction_count: int = 0
    retry_count: int = 0
    cost_note: str = ""
    memory_enabled_vs_baseline_delta: float | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.update(data.pop("extras", {}))
        return data


class SeraTimer:
    def __init__(self) -> None:
        self._start = time.perf_counter()

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._start) * 1000.0


def build_sera_record(
    *,
    runtime_ms: float,
    input_payload: Any,
    output_payload: Any,
    rigor_findings: list[dict[str, Any]],
    guard_decision: str,
    retry_count: int = 0,
    memory_delta: float | None = None,
    cost_note: str = "",
) -> SeraRecord:
    input_size = len(str(input_payload))
    output_size = len(str(output_payload))

    hold_count = sum(1 for f in rigor_findings if f["state"] == "HOLD")
    reverse_count = 1 if guard_decision == "REVERSE" else 0
    unsupported = sum(1 for f in rigor_findings if f["analyzer"] == "claim_support" and f["state"] != "PASS")
    source_missing = sum(1 for f in rigor_findings if f["analyzer"] == "source_presence" and f["state"] != "PASS")
    contradiction = sum(1 for f in rigor_findings if f["analyzer"] == "contradiction" and f["state"] != "PASS")

    return SeraRecord(
        runtime_ms=round(runtime_ms, 2),
        input_size=input_size,
        output_size=output_size,
        hold_count=hold_count,
        reverse_count=reverse_count,
        unsupported_claim_count=unsupported,
        source_missing_count=source_missing,
        contradiction_count=contradiction,
        retry_count=retry_count,
        cost_note=cost_note or "local stdlib runtime; no external API cost",
        memory_enabled_vs_baseline_delta=memory_delta,
    )