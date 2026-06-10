"""Light memory compression — preserve claims, scars, HOLDs, constraints."""

from __future__ import annotations

import re

from fractalish_ai.operational_self.models import CompressedMemory, MemoryEvent, new_id


def _dedupe_preserve(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def light_compress(event: MemoryEvent) -> CompressedMemory:
    claims = _dedupe_preserve(event.claims)
    decisions = _dedupe_preserve(event.decisions)
    constraints = _dedupe_preserve(event.provenance.get("operator_constraints", []))
    if event.operator_notes:
        constraints.append(event.operator_notes)

    open_loops = [
        c for c in claims
        if any(k in c.lower() for k in ("unresolved", "hold", "open", "pending"))
    ]
    scars = [
        c for c in claims
        if any(k in c.lower() for k in ("contradict", "scar", "similarity is not identity", "pressure is not truth"))
    ]

    raw = event.raw_summary or event.structured_summary
    sentences = [s.strip() for s in re.split(r"[.!?\n]+", raw) if s.strip()]
    unique_sentences: list[str] = []
    dropped: list[str] = []
    seen: set[str] = set()
    for s in sentences:
        norm = re.sub(r"\s+", " ", s.lower())
        if norm in seen:
            dropped.append(s)
            continue
        seen.add(norm)
        unique_sentences.append(s)

    summary_parts = unique_sentences[:6]
    if claims:
        summary_parts.extend(claims[:3])
    compressed_summary = ". ".join(summary_parts)[:800]

    return CompressedMemory(
        memory_id=new_id("mem"),
        source_event_id=event.event_id,
        activation_id=event.activation_id,
        compression_level="light",
        compressed_summary=compressed_summary,
        retained_claims=claims,
        retained_decisions=decisions,
        retained_constraints=constraints,
        retained_open_loops=open_loops,
        retained_scars=scars,
        retained_routes=[],
        dropped_noise=dropped[:20],
        compression_notes="Light compression: preserved claims, decisions, constraints, scars, HOLD-related loops",
        lossiness=0.1 if not dropped else min(0.35, 0.1 + len(dropped) * 0.02),
        replay_fidelity_estimate=max(0.75, 1.0 - (len(dropped) * 0.01)),
        confidence=event.confidence,
        uncertainty=event.uncertainty,
    )