"""API request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.enums import ExportFormat

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    sort: str = "score"
    order: str = Field(default="desc", pattern="^(asc|desc)$")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int
    pages: int


class OpportunityListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    organisation: str | None
    category: str | None
    location: str | None
    estimated_value: Decimal | None
    currency: str | None
    deadline_at: datetime | None
    score: int
    score_rating: str
    deadline_status: str
    status: str
    source_url: str | None
    first_seen_at: datetime
    last_seen_at: datetime


class OpportunityDetail(OpportunityListItem):
    source_id: uuid.UUID
    raw_opportunity_id: uuid.UUID | None
    external_id: str | None
    description: str | None
    summary: str | None
    country: str | None
    remote_status: str
    procurement_type: str
    contract_type: str
    minimum_value: Decimal | None
    maximum_value: Decimal | None
    published_at: datetime | None
    contact_name: str | None
    contact_email: str | None
    requirements: str | None
    skills: list[str]
    keywords: list[str]
    score_reasons: list[str]
    days_remaining: int | None
    content_hash: str
    created_at: datetime
    updated_at: datetime


class OpportunityFilters(BaseModel):
    min_score: int | None = Field(default=None, ge=0, le=100)
    max_score: int | None = Field(default=None, ge=0, le=100)
    source: str | None = None
    organisation: str | None = None
    keyword: str | None = None
    category: str | None = None
    status: str | None = None
    deadline_from: datetime | None = None
    deadline_to: datetime | None = None
    value_min: Decimal | None = None
    value_max: Decimal | None = None
    first_seen_from: datetime | None = None
    first_seen_to: datetime | None = None
    rating: str | None = None
    deadline_status: str | None = None


class SourceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    source_type: str
    enabled: bool
    description: str | None
    health_status: str
    consecutive_failures: int
    avg_response_ms: float | None
    last_http_status: int | None
    last_successful_run_at: datetime | None
    last_failed_run_at: datetime | None
    records_discovered: int
    records_accepted: int
    records_rejected: int


class RunStepRead(BaseModel):
    model_config = {"from_attributes": True}

    name: str
    status: str
    duration_ms: int | None
    details: dict[str, Any]
    error_message: str | None


class RunRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    status: str
    trigger: str
    started_at: datetime | None
    finished_at: datetime | None
    duration_ms: int | None
    source_filter: str | None
    metrics: dict[str, Any]
    error_message: str | None
    steps: list[RunStepRead] = Field(default_factory=list)


class RunCreate(BaseModel):
    source: str | None = None
    trigger: str = "api"


class ExportCreate(BaseModel):
    format: ExportFormat = ExportFormat.XLSX
    run_id: uuid.UUID | None = None


class ExportRead(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    format: str
    path: str
    record_count: int
    run_id: uuid.UUID | None
    created_at: datetime


class MetricsSummary(BaseModel):
    total_opportunities: int
    new_opportunities: int
    high_priority: int
    closing_soon: int
    expired: int
    sources_healthy: int
    sources_degraded: int
    sources_unhealthy: int
    last_run_id: uuid.UUID | None = None
    last_run_status: str | None = None
    last_run_duration_ms: int | None = None
    last_run_metrics: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ReadyResponse(BaseModel):
    status: str
    database: str
