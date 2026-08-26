"""Timezone-aware date parsing for ISO and UK formats."""

from __future__ import annotations

from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from dateutil import parser as date_parser

from app.core.constants import DEFAULT_TIMEZONE

_LONDON = ZoneInfo(DEFAULT_TIMEZONE)

_UK_FORMATS = (
    "%d/%m/%Y",
    "%d/%m/%y",
    "%d-%m-%Y",
    "%d-%m-%y",
    "%d %B %Y",
    "%d %b %Y",
    "%d %B %Y %H:%M",
    "%d/%m/%Y %H:%M",
)


def parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _ensure_aware(value)
    text = str(value).strip()
    if not text:
        return None
    for fmt in _UK_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
            return _ensure_aware(parsed)
        except ValueError:
            continue
    try:
        parsed = date_parser.parse(text, dayfirst=True)
        return _ensure_aware(parsed)
    except (ValueError, OverflowError, TypeError):
        return None


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        if value.hour == 0 and value.minute == 0 and value.second == 0:
            value = datetime.combine(value.date(), time(23, 59, 59))
        return value.replace(tzinfo=_LONDON).astimezone(UTC)
    return value.astimezone(UTC)


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def utcnow() -> datetime:
    return datetime.now(UTC)
