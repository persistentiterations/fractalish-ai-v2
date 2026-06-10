"""Transparent keyword/tag/link retrieval — no embeddings."""

from __future__ import annotations

import re

from fractalish_ai.operational_self.models import (
    CompressedMemory,
    ContradictionScar,
    MemoryAttractor,
    MemoryLink,
)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def retrieve(
    query: str,
    *,
    memories: dict[str, CompressedMemory],
    attractors: dict[str, MemoryAttractor],
    links: list[MemoryLink],
    scars: list[ContradictionScar],
    limit: int = 5,
) -> dict:
    q_tokens = _tokenize(query)
    q_lower = query.lower()
    results: list[dict] = []

    for attr in attractors.values():
        mem = memories.get(attr.memory_id)
        if not mem:
            continue
        text = " ".join([attr.label, mem.compressed_summary, " ".join(mem.retained_claims), " ".join(attr.tags)])
        tokens = _tokenize(text)
        overlap = q_tokens & tokens
        score = len(overlap) / max(len(q_tokens), 1)
        if q_lower in text.lower():
            score += 0.5
        for tag in attr.tags:
            if tag.lower() in q_lower or q_lower in tag.lower():
                score += 0.3
        if score < 0.15:
            continue

        warnings: list[str] = []
        guard_status = "WATCH"
        if "similarity means identity" in text.lower() or (
            "similarity" in q_lower and "identity" in q_lower
        ):
            warnings.append("Contradiction hazard: similarity is not identity")
            guard_status = "HOLD"
        related_scars = [s.scar_id for s in scars if attr.memory_id in s.memory_ids]
        if related_scars:
            warnings.append(f"Contradiction scars: {', '.join(related_scars)}")

        related_links = [
            l.link_id for l in links
            if l.from_memory_id == attr.memory_id or l.to_memory_id == attr.memory_id
        ]

        results.append(
            {
                "memory_id": attr.memory_id,
                "label": attr.label,
                "match_score": round(min(1.0, score), 3),
                "salience_score": attr.salience_score,
                "basin_region": attr.basin_region,
                "distance_from_center": attr.distance_from_reasoning_center,
                "guard_status": guard_status,
                "warnings": warnings,
                "links": related_links,
                "recommended_use": _recommend_use(attr),
                "compressed_summary": mem.compressed_summary[:200],
            }
        )

    results.sort(key=lambda r: (r["match_score"], r["salience_score"]), reverse=True)

    if "similarity" in q_lower and "identity" in q_lower and not any(r["warnings"] for r in results):
        results.insert(
            0,
            {
                "memory_id": "doctrine-warning",
                "label": "Similarity is not identity",
                "match_score": 1.0,
                "salience_score": 0.9,
                "basin_region": "scar",
                "distance_from_center": 0.25,
                "guard_status": "HOLD",
                "warnings": ["Doctrine: similarity is not identity — do not merge"],
                "links": [],
                "recommended_use": "HOLD — preserve distinction; do not collapse into identity",
                "compressed_summary": "Similarity is not identity. HOLD before false closure.",
            },
        )

    return {"query": query, "results": results[:limit], "total_matches": len(results)}


def _recommend_use(attr: MemoryAttractor) -> str:
    if attr.basin_region in ("fog", "scar"):
        return "Review with HOLD awareness — not for automatic truth"
    if attr.basin_region in ("core", "active"):
        return "Core continuity reference — route through RIGOR/GUARD"
    return "Peripheral context — lower commitment retrieval"