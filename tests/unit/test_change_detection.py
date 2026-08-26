"""Change detection tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

from app.schemas.opportunity import NormalisedOpportunity
from app.services.change_detection.engine import ChangeDetectionEngine


def test_updated_deadline_and_value_are_major() -> None:
    existing = SimpleNamespace(
        title="Python Data Extraction Automation",
        organisation="Northbridge Digital Services",
        description="Original description",
        requirements="Python",
        status="open",
        deadline_at=datetime(2026, 10, 1, tzinfo=UTC),
        estimated_value=Decimal("50000"),
        minimum_value=Decimal("50000"),
        maximum_value=Decimal("50000"),
        location="London",
        source_url="https://opportunities.example.invalid/x",
        category="automation",
        contract_type="contract",
    )
    incoming = NormalisedOpportunity(
        source_name="demo",
        title=existing.title,
        organisation=existing.organisation,
        description=existing.description + " Deadline brought forward by the buyer.",
        requirements=existing.requirements,
        status="open",
        deadline_at=datetime(2026, 9, 1, tzinfo=UTC),
        estimated_value=Decimal("125000"),
        minimum_value=Decimal("125000"),
        maximum_value=Decimal("125000"),
        location="London",
        source_url=existing.source_url,
        category="automation",
        contract_type="contract",
        content_hash="a" * 64,
        fingerprint="b" * 64,
    )
    engine = ChangeDetectionEngine()
    changes = engine.diff(existing, incoming)  # type: ignore[arg-type]
    fields = {change["field_name"] for change in changes}
    assert "deadline_at" in fields
    assert "estimated_value" in fields
    assert engine.is_major(changes) is True
