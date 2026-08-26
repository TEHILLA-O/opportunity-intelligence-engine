"""Shared constants."""

from decimal import Decimal

APP_SLUG = "opportunity-engine"
DEFAULT_CURRENCY = "GBP"
DEFAULT_COUNTRY = "United Kingdom"
DEFAULT_TIMEZONE = "Europe/London"

CONTENT_HASH_ALGORITHM = "sha256"

# Deduplication thresholds (deterministic, documented in ADR 006)
EXACT_MATCH_CONFIDENCE = Decimal("1.00")
CONFIRMED_DUPLICATE_THRESHOLD = Decimal("0.85")
AMBIGUOUS_DUPLICATE_THRESHOLD = Decimal("0.65")

# Deadline windows in days
DEADLINE_CRITICAL_DAYS = 1
DEADLINE_URGENT_DAYS = 3
DEADLINE_UPCOMING_DAYS = 7
DEADLINE_NORMAL_DAYS = 14

# Score rating bands
RATING_VERY_HIGH = 80
RATING_HIGH = 65
RATING_MEDIUM = 45
RATING_LOW = 25

# Change-detection fields that constitute a "major" change
MAJOR_CHANGE_FIELDS = frozenset(
    {
        "deadline_at",
        "estimated_value",
        "minimum_value",
        "maximum_value",
        "status",
        "organisation",
        "description",
        "requirements",
    }
)

TRACKED_CHANGE_FIELDS = (
    "title",
    "organisation",
    "description",
    "requirements",
    "status",
    "deadline_at",
    "estimated_value",
    "minimum_value",
    "maximum_value",
    "location",
    "source_url",
    "category",
    "contract_type",
)

MAX_SUMMARY_LENGTH = 400
MAX_TITLE_LENGTH = 500
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

SENSITIVE_LOG_KEYS = frozenset(
    {
        "password",
        "smtp_password",
        "secret",
        "secret_key",
        "token",
        "authorization",
        "api_key",
        "database_url",
    }
)
