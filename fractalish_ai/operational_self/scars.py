"""Contradiction scar detection and management."""

from __future__ import annotations

from fractalish_ai.operational_self.models import CompressedMemory, ContradictionScar, MemoryEvent, new_id, utc_now

CONTRADICTION_PAIRS = [
    ("similarity is not identity", "similarity means identity"),
    ("pressure is not truth", "pressure increases truth"),
    ("a passed scan is not permission for memory", "safe for ai memory"),
    ("authority is scoped", "applies everywhere"),
]


def detect_scars_from_event(event: MemoryEvent, memory: CompressedMemory) -> list[ContradictionScar]:
    scars: list[ContradictionScar] = []
    text = " ".join(memory.retained_claims + [memory.compressed_summary, event.raw_summary]).lower()
    now = utc_now()

    claim_lower = [c.lower() for c in memory.retained_claims]
    for a, b in CONTRADICTION_PAIRS:
        both_present = (a in text and b in text) or (a in claim_lower and b in claim_lower)
        if not both_present:
            continue
            scars.append(
                ContradictionScar(
                    scar_id=new_id("scar"),
                    memory_ids=[memory.memory_id],
                    claim_a=a,
                    claim_b=b,
                    severity="high" if "similarity" in a or "pressure" in a else "medium",
                    first_seen=now,
                    last_seen=now,
                    status="hold" if "similarity means identity" in text else "unresolved",
                    guard_effect="HOLD",
                    replay_warning=f"Contradiction preserved: {a} vs {b}",
                    notes="Scar must not be erased during compression",
                )
            )

    if "contradiction" in event.tags and len(memory.retained_claims) >= 2:
        scars.append(
            ContradictionScar(
                scar_id=new_id("scar"),
                memory_ids=[memory.memory_id],
                claim_a=memory.retained_claims[0],
                claim_b=memory.retained_claims[1],
                severity="high",
                first_seen=now,
                last_seen=now,
                status="hold",
                guard_effect="HOLD",
                replay_warning="Tagged contradiction — scar preserved",
            )
        )

    if event.guard_status == "REVERSE" and "exfiltration" in text:
        scars.append(
            ContradictionScar(
                scar_id=new_id("scar"),
                memory_ids=[memory.memory_id],
                claim_a="governed intake required",
                claim_b="data exfiltration attempted",
                severity="critical",
                first_seen=now,
                last_seen=now,
                status="hold",
                guard_effect="REVERSE",
                replay_warning="Hostile intake scar — do not merge into trusted memory",
            )
        )
    return scars