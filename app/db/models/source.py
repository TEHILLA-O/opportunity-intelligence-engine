"""Source registry and health tracking."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.core.enums import SourceHealthStatus, SourceType
from app.db.base_class import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.db.models.opportunity import Opportunity, RawOpportunity
    from app.db.models.run import IngestionError


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(40), nullable=False, default=SourceType.MOCK)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    last_successful_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_failed_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_response_ms: Mapped[float | None] = mapped_column(nullable=True)
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_accepted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    health_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SourceHealthStatus.UNKNOWN, index=True
    )

    raw_opportunities: Mapped[list[RawOpportunity]] = relationship(back_populates="source")
    opportunities: Mapped[list[Opportunity]] = relationship(back_populates="source")
    ingestion_errors: Mapped[list[IngestionError]] = relationship(back_populates="source")
