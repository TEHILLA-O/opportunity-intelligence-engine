"""Export audit records."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON, Uuid

from app.core.enums import ExportFormat
from app.db.base_class import Base, TimestampMixin, new_uuid


class ExportRecord(TimestampMixin, Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    format: Mapped[str] = mapped_column(String(10), nullable=False, default=ExportFormat.XLSX)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("automation_runs.id"), nullable=True
    )
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
