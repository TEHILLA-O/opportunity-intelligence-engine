"""Reporting facade used by the pipeline, CLI and API."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.enums import ExportFormat
from app.db.models.opportunity import Opportunity
from app.services.reporting.excel import ExcelReportBuilder
from app.services.reporting.tabular import TabularExporter


class ReportingService:
    def __init__(self) -> None:
        self.excel = ExcelReportBuilder()
        self.tabular = TabularExporter()

    def export_all(
        self,
        opportunities: Sequence[Opportunity],
        metrics: dict[str, Any],
        run_id: UUID | None = None,
    ) -> Path:
        return self.excel.build(opportunities, metrics, run_id=run_id)

    def export(
        self,
        opportunities: Sequence[Opportunity],
        fmt: ExportFormat,
        metrics: dict[str, Any] | None = None,
        run_id: UUID | None = None,
    ) -> Path:
        if fmt == ExportFormat.XLSX:
            return self.excel.build(opportunities, metrics or {}, run_id=run_id)
        if fmt == ExportFormat.CSV:
            return self.tabular.export_csv(opportunities)
        return self.tabular.export_json(opportunities)
