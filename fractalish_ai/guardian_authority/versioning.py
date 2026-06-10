"""Version matching for authority records."""

from __future__ import annotations

from fractalish_ai.guardian_authority.models import AuthorityRecord


def parse_version(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for segment in version.replace("-", ".").split("."):
        segment = segment.strip().lower().lstrip("v")
        if segment.isdigit():
            parts.append(int(segment))
        elif segment:
            parts.append(0)
    return tuple(parts) if parts else (0,)


def version_match(record: AuthorityRecord, required_version: str = "") -> bool:
    if not required_version:
        return not record.superseded_by
    return parse_version(record.version) >= parse_version(required_version) and not record.superseded_by


def is_outdated(record: AuthorityRecord, current_version: str = "2.0") -> bool:
    if record.superseded_by:
        return True
    return parse_version(record.version) < parse_version(current_version)


def version_conflict_note(record_a: AuthorityRecord, record_b: AuthorityRecord) -> str:
    if record_a.supersedes == record_b.record_id or record_b.supersedes == record_a.record_id:
        return f"Version chain: {record_a.version} vs {record_b.version}"
    if record_a.version != record_b.version and record_a.title == record_b.title:
        return f"Same title, different versions: {record_a.version} vs {record_b.version}"
    return ""