"""Normalised opportunity schemas used inside the pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.enums import (
    ContractType,
    DeadlineStatus,
    OpportunityStatus,
    ProcurementType,
    RemoteStatus,
    ScoreRating,
)


class NormalisedOpportunity(BaseModel):
    source_name: str
    external_id: str | None = None
    title: str
    organisation: str | None = None
    description: str | None = None
    summary: str | None = None
    category: str | None = None
    location: str | None = None
    country: str | None = None
    remote_status: RemoteStatus = RemoteStatus.UNKNOWN
    procurement_type: ProcurementType = ProcurementType.OTHER
    contract_type: ContractType = ContractType.UNKNOWN
    currency: str | None = None
    minimum_value: Decimal | None = None
    maximum_value: Decimal | None = None
    estimated_value: Decimal | None = None
    published_at: datetime | None = None
    deadline_at: datetime | None = None
    source_url: str | None = None
    canonical_url: str | None = None
    contact_name: str | None = None
    contact_email: EmailStr | None = None
    requirements: str | None = None
    skills: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    status: OpportunityStatus = OpportunityStatus.OPEN
    content_hash: str
    fingerprint: str
    normalised_title: str | None = None
    normalised_organisation: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def _currency_iso(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().upper()
        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return cleaned

    @field_validator("title")
    @classmethod
    def _title_present(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("title is required")
        return value.strip()


class ScoredOpportunity(NormalisedOpportunity):
    score: int = Field(ge=0, le=100)
    score_rating: ScoreRating
    score_reasons: list[str] = Field(default_factory=list)
    deadline_status: DeadlineStatus = DeadlineStatus.UNKNOWN
    days_remaining: int | None = None


class OpportunityRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    source_id: uuid.UUID
    raw_opportunity_id: uuid.UUID | None
    external_id: str | None
    title: str
    organisation: str | None
    description: str | None
    summary: str | None
    category: str | None
    location: str | None
    country: str | None
    remote_status: str
    procurement_type: str
    contract_type: str
    currency: str | None
    minimum_value: Decimal | None
    maximum_value: Decimal | None
    estimated_value: Decimal | None
    published_at: datetime | None
    deadline_at: datetime | None
    source_url: str | None
    contact_name: str | None
    contact_email: str | None
    requirements: str | None
    skills: list[str]
    keywords: list[str]
    status: str
    score: int
    score_rating: str
    score_reasons: list[str]
    deadline_status: str
    days_remaining: int | None
    first_seen_at: datetime
    last_seen_at: datetime
    content_hash: str
    created_at: datetime
    updated_at: datetime
