"""Opportunity, raw provenance, history and duplicate candidate models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from app.core.enums import (
    ContractType,
    DeadlineStatus,
    DuplicateStatus,
    OpportunityStatus,
    ProcurementType,
    RemoteStatus,
    ScoreRating,
)
from app.db.base_class import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from app.db.models.run import AutomationRun
    from app.db.models.source import Source


class RawOpportunity(TimestampMixin, Base):
    """Immutable-enough provenance layer: what was collected, before normalisation."""

    __tablename__ = "raw_opportunities"
    __table_args__ = (
        Index("ix_raw_source_external", "source_id", "external_id"),
        Index("ix_raw_content_hash", "content_hash"),
        Index("ix_raw_run_id", "run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("automation_runs.id"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    raw_title: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_organisation: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_deadline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    http_headers: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    source: Mapped[Source] = relationship(back_populates="raw_opportunities")
    opportunity: Mapped[Opportunity | None] = relationship(back_populates="raw_opportunity")


class Opportunity(TimestampMixin, Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_opportunity_source_external"),
        Index("ix_opportunity_score", "score"),
        Index("ix_opportunity_deadline", "deadline_at"),
        Index("ix_opportunity_status", "status"),
        Index("ix_opportunity_rating", "score_rating"),
        Index("ix_opportunity_first_seen", "first_seen_at"),
        Index("ix_opportunity_org", "organisation"),
        Index("ix_opportunity_hash", "content_hash"),
        Index("ix_opportunity_canonical_url", "canonical_url"),
        Index("ix_opportunity_fingerprint", "fingerprint"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("sources.id"), nullable=False, index=True
    )
    raw_opportunity_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("raw_opportunities.id"), nullable=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    organisation: Mapped[str | None] = mapped_column(String(300), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    remote_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RemoteStatus.UNKNOWN
    )
    procurement_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ProcurementType.OTHER
    )
    contract_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default=ContractType.UNKNOWN
    )
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    minimum_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    maximum_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OpportunityStatus.OPEN, index=True
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    score_rating: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ScoreRating.VERY_LOW
    )
    score_reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    deadline_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DeadlineStatus.UNKNOWN
    )
    days_remaining: Mapped[int | None] = mapped_column(Integer, nullable=True)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    normalised_title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    normalised_organisation: Mapped[str | None] = mapped_column(String(300), nullable=True)

    source: Mapped[Source] = relationship(back_populates="opportunities")
    raw_opportunity: Mapped[RawOpportunity | None] = relationship(back_populates="opportunity")
    history: Mapped[list[OpportunityHistory]] = relationship(back_populates="opportunity")


class OpportunityHistory(Base):
    __tablename__ = "opportunity_history"
    __table_args__ = (Index("ix_history_opportunity_detected", "opportunity_id", "detected_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("opportunities.id"), nullable=False, index=True
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("automation_runs.id"), nullable=True
    )
    field_name: Mapped[str] = mapped_column(String(80), nullable=False)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    opportunity: Mapped[Opportunity] = relationship(back_populates="history")
    run: Mapped[AutomationRun | None] = relationship()


class DuplicateCandidate(TimestampMixin, Base):
    __tablename__ = "duplicate_candidates"
    __table_args__ = (
        Index("ix_dup_left_right", "opportunity_id", "candidate_id"),
        UniqueConstraint("opportunity_id", "candidate_id", name="uq_duplicate_pair"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=new_uuid)
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("opportunities.id"), nullable=False
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("opportunities.id"), nullable=False
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DuplicateStatus.AMBIGUOUS
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
