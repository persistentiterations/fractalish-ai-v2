"""Dashboard summary export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_dashboard(
    path: Path,
    *,
    self_state: dict,
    narrative_frame: dict,
    attractors: list[dict],
    memories: list[dict],
    links: list[dict],
    scars: list[dict],
    fog_regions: list[dict],
    replay_routes: list[dict],
    fmm_snapshot: dict,
    retrieval_samples: list[dict],
    decay_log: list[dict],
    audit_timeline: list[dict],
) -> Path:
    payload: dict[str, Any] = {
        "operational_self_state": self_state,
        "narrative_frame": narrative_frame,
        "core_attractors": [a for a in attractors if a.get("basin_region") == "core"],
        "active_attractors": [a for a in attractors if a.get("basin_region") in ("core", "active")],
        "peripheral_attractors": [a for a in attractors if a.get("basin_region") in ("peripheral", "dormant")],
        "all_attractors": attractors,
        "memories": memories,
        "memory_links": links,
        "contradiction_scars": scars,
        "fog_regions": fog_regions,
        "replay_routes": replay_routes,
        "fractal_memory_map_snapshot": fmm_snapshot,
        "retrieval_samples": retrieval_samples,
        "decay_log": decay_log,
        "audit_timeline": audit_timeline,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path