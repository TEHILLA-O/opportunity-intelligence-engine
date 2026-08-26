"""Record-level validation prior to persistence."""

from __future__ import annotations

from app.core.exceptions import RecordValidationError
from app.core.security import is_public_http_url
from app.schemas.opportunity import NormalisedOpportunity
from app.schemas.raw import RawOpportunityIn


class ValidationEngine:
    def validate_raw(self, raw: RawOpportunityIn) -> None:
        if not raw.source_name:
            raise RecordValidationError("source_name is required")
        if not raw.raw_title or not raw.raw_title.strip():
            raise RecordValidationError(
                "title is required",
                details={"source": raw.source_name, "external_id": raw.external_id},
            )
        if raw.source_url and raw.source_url.startswith(("http://", "https://")):
            if not is_public_http_url(raw.source_url):
                raise RecordValidationError(
                    "Invalid URL",
                    details={"source_url": raw.source_url, "source": raw.source_name},
                )

    def validate_normalised(self, record: NormalisedOpportunity) -> None:
        if record.minimum_value is not None and record.maximum_value is not None:
            if record.minimum_value > record.maximum_value:
                raise RecordValidationError(
                    "minimum_value cannot exceed maximum_value",
                    details={"external_id": record.external_id},
                )
        if record.published_at and record.deadline_at:
            if record.published_at > record.deadline_at:
                # Not fatal enough to drop the record; clamp is handled by callers if needed.
                pass
        if record.source_url and record.source_url.startswith(("http://", "https://")):
            if not is_public_http_url(record.source_url):
                raise RecordValidationError(
                    "Invalid source URL", details={"url": record.source_url}
                )
