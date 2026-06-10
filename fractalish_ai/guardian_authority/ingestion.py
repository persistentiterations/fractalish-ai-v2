"""Authority corpus ingestion from local JSON files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fractalish_ai.guardian_authority.models import AuthorityRecord, AuthoritySource, new_id, utc_now

REQUIRED_SOURCE = {"source_id", "source_name", "source_type", "publisher", "authority_level", "jurisdiction"}
REQUIRED_RECORD = {"record_id", "source_id", "title", "record_type", "text"}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def load_corpus_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_corpus_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source = payload.get("source", {})
    missing = REQUIRED_SOURCE - set(source.keys())
    if missing:
        errors.append(f"Source missing fields: {sorted(missing)}")
    for idx, rec in enumerate(payload.get("records", [])):
        rec_missing = REQUIRED_RECORD - set(rec.keys())
        if rec_missing:
            errors.append(f"Record {idx} missing fields: {sorted(rec_missing)}")
    return errors


def parse_source(data: dict[str, Any]) -> AuthoritySource:
    if not data.get("retrieved_at"):
        data = {**data, "retrieved_at": utc_now()}
    return AuthoritySource(**{k: v for k, v in data.items() if k in AuthoritySource.__dataclass_fields__})


def parse_record(data: dict[str, Any]) -> AuthorityRecord:
    if not data.get("normalized_text"):
        data = {**data, "normalized_text": normalize_text(data.get("text", ""))}
    return AuthorityRecord(**{k: v for k, v in data.items() if k in AuthorityRecord.__dataclass_fields__})


def ingest_file(path: Path) -> tuple[AuthoritySource, list[AuthorityRecord]]:
    payload = load_corpus_file(path)
    errors = validate_corpus_payload(payload)
    if errors:
        raise ValueError("; ".join(errors))
    source = parse_source(payload["source"])
    records = [parse_record(r) for r in payload.get("records", [])]
    return source, records