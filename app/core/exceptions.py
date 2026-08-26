"""Application-specific exception hierarchy."""

from __future__ import annotations


class OpportunityEngineError(Exception):
    """Base error for the Opportunity Engine."""

    def __init__(self, message: str, *, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(OpportunityEngineError):
    """Invalid application or source configuration."""


class SourceError(OpportunityEngineError):
    """A source connector failed while collecting data."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, details=details)
        self.source = source


class SourceTimeoutError(SourceError):
    """A source exceeded its configured timeout."""


class SourceRateLimitError(SourceError):
    """A source returned HTTP 429 or otherwise rate-limited the client."""


class SourceHttpError(SourceError):
    """A source returned a non-success HTTP status."""

    def __init__(
        self,
        message: str,
        *,
        source: str | None = None,
        status_code: int | None = None,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message, source=source, details=details)
        self.status_code = status_code


class ExtractionError(OpportunityEngineError):
    """Failed to extract structured records from a raw payload."""


class RecordValidationError(OpportunityEngineError):
    """A single record failed schema or business validation."""


class NormalisationError(OpportunityEngineError):
    """Failed to normalise a field or record."""


class RepositoryError(OpportunityEngineError):
    """Persistence layer failure."""


class ScoringError(OpportunityEngineError):
    """Scoring engine failure."""


class ExportError(OpportunityEngineError):
    """Report or export generation failure."""


class NotificationError(OpportunityEngineError):
    """Notification delivery failure."""


class DuplicateError(OpportunityEngineError):
    """Deduplication engine failure."""
