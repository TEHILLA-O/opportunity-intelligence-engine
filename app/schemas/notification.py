"""Notification payload schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Notification(BaseModel):
    event: str
    timestamp: datetime
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    opportunity_id: UUID | None = None
    run_id: UUID | None = None


class NotificationResult(BaseModel):
    provider: str
    success: bool
    message: str = "ok"
