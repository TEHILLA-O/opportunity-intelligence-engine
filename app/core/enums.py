"""Shared enumerations used across models, schemas and services."""

from enum import StrEnum


class SourceType(StrEnum):
    MOCK = "mock"
    JSON = "json"
    RSS = "rss"
    HTML = "html"
    PLAYWRIGHT = "playwright"


class SourceHealthStatus(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class OpportunityStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    EXPIRED = "expired"
    AWARDED = "awarded"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ScoreRating(StrEnum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


class DeadlineStatus(StrEnum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    UPCOMING = "UPCOMING"
    NORMAL = "NORMAL"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


class ContractType(StrEnum):
    FIXED_PRICE = "fixed_price"
    TIME_AND_MATERIALS = "time_and_materials"
    FRAMEWORK = "framework"
    CALL_OFF = "call_off"
    GRANT = "grant"
    CONTRACT = "contract"
    SUBCONTRACT = "subcontract"
    RFQ = "rfq"
    UNKNOWN = "unknown"


class RemoteStatus(StrEnum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class ProcurementType(StrEnum):
    TENDER = "tender"
    RFQ = "rfq"
    GRANT = "grant"
    FRAMEWORK = "framework"
    SUBCONTRACT = "subcontract"
    FREELANCE = "freelance"
    SUPPLIER = "supplier"
    OTHER = "other"


class DuplicateStatus(StrEnum):
    CONFIRMED = "confirmed"
    AMBIGUOUS = "ambiguous"
    REJECTED = "rejected"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    SKIPPED = "skipped"


class NotificationEvent(StrEnum):
    HIGH_PRIORITY = "high_priority_opportunity"
    CLOSING_SOON = "deadline_closing_soon"
    NEW_HIGH_PRIORITY = "new_high_priority_opportunity"
    MAJOR_CHANGE = "major_opportunity_change"
    SOURCE_FAILING = "source_repeatedly_failing"


class NotificationStatus(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExportFormat(StrEnum):
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"


class RunTrigger(StrEnum):
    CLI = "cli"
    API = "api"
    SCHEDULE = "schedule"
    DEMO = "demo"
    TEST = "test"
