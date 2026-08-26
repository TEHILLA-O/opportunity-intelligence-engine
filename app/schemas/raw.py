"""Raw opportunity payloads collected from source connectors."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RawOpportunityIn(BaseModel):
    """Connector output before validation and normalisation."""

    source_name: str
    external_id: str | None = None
    source_url: str | None = None
    retrieved_at: datetime
    raw_title: str | None = None
    raw_description: str | None = None
    raw_organisation: str | None = None
    raw_location: str | None = None
    raw_value: str | None = None
    raw_deadline: str | None = None
    raw_category: str | None = None
    raw_contact_name: str | None = None
    raw_contact_email: str | None = None
    raw_requirements: str | None = None
    raw_skills: list[str] = Field(default_factory=list)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)
    http_status: int | None = None
    http_headers: dict[str, Any] | None = None
    content_hash: str | None = None


class SourceHealth(BaseModel):
    name: str
    healthy: bool
    status_code: int | None = None
    latency_ms: float | None = None
    message: str = "ok"
    details: dict[str, Any] = Field(default_factory=dict)
