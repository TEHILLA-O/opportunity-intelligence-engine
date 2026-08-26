"""CSV and JSON export helpers."""

from __future__ import annotations

import csv
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.exceptions import ExportError
from app.db.models.opportunity import Opportunity
from app.services.normalisation.dates import utcnow


def _row(item: Opportunity) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "title": item.title,
        "organisation": item.organisation,
        "score": item.score,
        "score_rating": item.score_rating,
        "deadline_at": item.deadline_at.isoformat() if item.deadline_at else None,
        "deadline_status": item.deadline_status,
        "estimated_value": str(item.estimated_value) if item.estimated_value is not None else None,
        "currency": item.currency,
        "location": item.location,
        "category": item.category,
        "status": item.status,
        "source_url": item.source_url,
        "first_seen_at": item.first_seen_at.isoformat() if item.first_seen_at else None,
        "score_reasons": item.score_reasons,
    }


class TabularExporter:
    def export_csv(self, opportunities: Sequence[Opportunity], *, path: Path | None = None) -> Path:
        settings = get_settings()
        settings.ensure_data_dirs()
        target = (
            path or settings.exports_dir / f"opportunities_{utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        rows = [_row(item) for item in opportunities]
        if not rows:
            fieldnames = ["id", "title"]
        else:
            fieldnames = list(rows[0].keys())
        try:
            with target.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    flat = dict(row)
                    if isinstance(flat.get("score_reasons"), list):
                        flat["score_reasons"] = " | ".join(flat["score_reasons"])
                    writer.writerow(flat)
            return target
        except Exception as exc:
            raise ExportError(f"CSV export failed: {exc}") from exc

    def export_json(
        self, opportunities: Sequence[Opportunity], *, path: Path | None = None
    ) -> Path:
        settings = get_settings()
        settings.ensure_data_dirs()
        target = (
            path
            or settings.exports_dir / f"opportunities_{utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        try:
            target.write_text(
                json.dumps([_row(item) for item in opportunities], indent=2), encoding="utf-8"
            )
            return target
        except Exception as orig:
            raise ExportError(f"JSON export failed: {orig}") from orig
