"""Excel export tests."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.services.reporting.excel import ExcelReportBuilder


def test_excel_creation(tmp_path) -> None:
    item = SimpleNamespace(
        id=uuid4(),
        title="Python Data Extraction Automation",
        organisation="Northbridge Digital Services",
        score=87,
        score_rating="VERY_HIGH",
        deadline_at=datetime(2026, 9, 1, tzinfo=UTC),
        deadline_status="UPCOMING",
        estimated_value=Decimal("85000.00"),
        currency="GBP",
        location="Remote",
        category="automation",
        status="open",
        source_url="https://opportunities.example.invalid/demo/1",
        first_seen_at=datetime.now(UTC),
        score_reasons=["Python keyword match: +15"],
        source_id=uuid4(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    path = tmp_path / "report.xlsx"
    result = ExcelReportBuilder().build(
        [item], {"new_records": 1, "duration_seconds": 1.2}, path=path
    )
    assert result.exists()
    assert result.stat().st_size > 1000
