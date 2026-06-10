"""License evaluation for authority sources and records."""

from __future__ import annotations

from fractalish_ai.guardian_authority.models import AuthorityRecord, AuthoritySource, LicenseStatus

BLOCKED_LICENSES: set[LicenseStatus] = {"proprietary_restricted", "paid_api_required", "unknown"}


def license_allowed(source: AuthoritySource, record: AuthorityRecord) -> bool:
    status = record.license_status or source.license_status
    return status not in BLOCKED_LICENSES


def license_status_for_route(source: AuthoritySource, record: AuthorityRecord) -> bool:
    if source.license_status in BLOCKED_LICENSES:
        return False
    if record.license_status in BLOCKED_LICENSES:
        return False
    return True