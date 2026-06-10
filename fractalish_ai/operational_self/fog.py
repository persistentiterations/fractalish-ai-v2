"""Fog / HOLD region management."""

from __future__ import annotations

from fractalish_ai.operational_self.models import CompressedMemory, FogRegion, MemoryEvent, new_id, utc_now


def detect_fog_from_event(event: MemoryEvent, memory: CompressedMemory) -> FogRegion | None:
    if event.guard_status not in ("HOLD", "REVERSE", "WATCH"):
        return None
    if event.importance_hint >= 0.8 and event.guard_status == "WATCH":
        return None

    missing = list(event.provenance.get("missing_context", []))
    if event.guard_status == "HOLD":
        missing.append("guard_hold_unresolved")

    return FogRegion(
        fog_id=new_id("fog"),
        label=event.structured_summary[:60] or memory.compressed_summary[:60],
        related_memory_ids=[memory.memory_id],
        reason=f"Unresolved guard status: {event.guard_status}",
        missing_context=missing,
        guard_status=event.guard_status,
        created_at=utc_now(),
        review_needed=True,
        next_action="Resolve HOLD before false closure.",
    )