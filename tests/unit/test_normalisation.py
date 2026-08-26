"""Normalisation unit tests."""

from __future__ import annotations

from datetime import UTC
from decimal import Decimal

import pytest
from app.core.exceptions import RecordValidationError
from app.schemas.raw import RawOpportunityIn
from app.services.deadlines.engine import DeadlineEngine
from app.services.normalisation.currency import parse_currency_code, parse_money
from app.services.normalisation.dates import parse_datetime, utcnow
from app.services.normalisation.engine import NormalisationEngine
from app.services.normalisation.text import canonical_url, collapse_whitespace, extract_emails


def test_currency_gbp_symbol() -> None:
    minimum, maximum, estimated, currency = parse_money("£12,500")
    assert currency == "GBP"
    assert estimated == Decimal("12500")
    assert minimum == maximum == Decimal("12500")


def test_currency_range() -> None:
    minimum, maximum, estimated, currency = parse_money("GBP 10000 - 20000")
    assert currency == "GBP"
    assert minimum == Decimal("10000")
    assert maximum == Decimal("20000")
    assert estimated == Decimal("15000")


def test_malformed_currency_does_not_raise() -> None:
    minimum, maximum, estimated, currency = parse_money("approx lots of money")
    assert minimum is None
    assert estimated is None
    assert currency is None


def test_currency_code_iso() -> None:
    assert parse_currency_code("usd") == "USD"


def test_iso_date() -> None:
    parsed = parse_datetime("2026-09-01")
    assert parsed is not None
    assert parsed.tzinfo is not None
    assert parsed.astimezone(UTC).year == 2026


def test_uk_date() -> None:
    parsed = parse_datetime("31/12/2026")
    assert parsed is not None
    assert parsed.month == 12
    assert parsed.day == 31


def test_deadline_expired() -> None:
    past = parse_datetime("01/01/2020")
    evaluation = DeadlineEngine().evaluate(past)
    assert evaluation.expired is True
    assert evaluation.status.value == "EXPIRED"


def test_whitespace_and_emails() -> None:
    assert collapse_whitespace("  too   many   spaces ") == "too many spaces"
    assert extract_emails("Contact  jane.doe@eastmere.example please") == [
        "jane.doe@eastmere.example"
    ]


def test_canonical_url_strips_tracking() -> None:
    assert (
        canonical_url("https://WWW.Example.COM/path/?utm_source=x&id=1")
        == "https://example.com/path?id=1"
    )


def test_missing_title_raises() -> None:
    engine = NormalisationEngine()
    raw = RawOpportunityIn(
        source_name="demo",
        retrieved_at=utcnow(),
        raw_title="  ",
        source_url="https://opportunities.example.invalid/x",
    )
    with pytest.raises(RecordValidationError):
        engine.normalise(raw)


def test_invalid_url_raises() -> None:
    engine = NormalisationEngine()
    raw = RawOpportunityIn(
        source_name="demo",
        retrieved_at=utcnow(),
        raw_title="Broken URL Procurement Feed",
        source_url="notaurl",
    )
    with pytest.raises(RecordValidationError):
        engine.normalise(raw)
