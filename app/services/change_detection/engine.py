"""Incremental change detection against stored opportunities."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.constants import MAJOR_CHANGE_FIELDS, TRACKED_CHANGE_FIELDS
from app.db.models.opportunity import Opportunity
from app.schemas.opportunity import NormalisedOpportunity
from app.services.normalisation.dates import ensure_utc, utcnow


def _stringify(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        aware = ensure_utc(value)
        return aware.isoformat() if aware else None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


class ChangeDetectionEngine:
    def diff(
        self, existing: Opportunity, incoming: NormalisedOpportunity
    ) -> list[dict[str, str | None]]:
        changes: list[dict[str, str | None]] = []
        for field in TRACKED_CHANGE_FIELDS:
            old = _stringify(getattr(existing, field, None))
            new = _stringify(getattr(incoming, field, None))
            if old != new:
                changes.append(
                    {
                        "field_name": field,
                        "previous_value": old,
                        "new_value": new,
                        "detected_at": utcnow().isoformat(),
                    }
                )
        return changes

    def is_major(self, changes: list[dict[str, str | None]]) -> bool:
        return any(change["field_name"] in MAJOR_CHANGE_FIELDS for change in changes)
