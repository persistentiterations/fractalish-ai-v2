"""Memory event ingestion from local JSON samples."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fractalish_ai.operational_self.models import MemoryEvent, utc_now


def load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_events(bundle: dict[str, Any], default_activation: str = "") -> list[MemoryEvent]:
    activation = bundle.get("activation_id", default_activation) or "act-default"
    events: list[MemoryEvent] = []
    for raw in bundle.get("events", []):
        if not raw.get("timestamp"):
            raw = {**raw, "timestamp": utc_now()}
        if not raw.get("activation_id"):
            raw = {**raw, "activation_id": activation}
        fields = {k: v for k, v in raw.items() if k in MemoryEvent.__dataclass_fields__}
        events.append(MemoryEvent(**fields))
    return events


def ingest_file(path: Path) -> tuple[dict[str, Any], list[MemoryEvent]]:
    bundle = load_bundle(path)
    events = parse_events(bundle)
    return bundle, events