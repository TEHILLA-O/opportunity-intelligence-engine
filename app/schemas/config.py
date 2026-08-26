"""Source and scoring configuration schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import SourceType


class SourceConfig(BaseModel):
    enabled: bool = True
    type: SourceType
    description: str | None = None
    url: str | None = None
    path: str | None = None
    delay_seconds: float | None = Field(default=None, ge=0)
    timeout_seconds: float | None = Field(default=None, gt=0)
    max_retries: int | None = Field(default=None, ge=0)
    respect_robots: bool | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_locator(self) -> SourceConfig:
        if self.type in {SourceType.JSON, SourceType.RSS, SourceType.HTML, SourceType.PLAYWRIGHT}:
            if not self.url and not self.path:
                raise ValueError(f"{self.type} sources require a url or path")
        return self


class SourcesFile(BaseModel):
    sources: dict[str, SourceConfig]

    @field_validator("sources")
    @classmethod
    def _non_empty(cls, value: dict[str, SourceConfig]) -> dict[str, SourceConfig]:
        if not value:
            raise ValueError("at least one source must be defined")
        return value


class ScoringConfig(BaseModel):
    keywords: dict[str, int] = Field(default_factory=dict)
    excluded_keywords: dict[str, int] = Field(default_factory=dict)
    preferred_contract_types: dict[str, int] = Field(default_factory=dict)
    preferred_categories: dict[str, int] = Field(default_factory=dict)
    preferred_locations: dict[str, int] = Field(default_factory=dict)
    preferred_procurement_types: dict[str, int] = Field(default_factory=dict)
    required_skills: dict[str, int] = Field(default_factory=dict)
    remote_bonus: int = 10
    hybrid_bonus: int = 5
    minimum_value: int | None = None
    maximum_value: int | None = None
    value_in_range_bonus: int = 10
    deadline_min_days: int = 3
    deadline_max_days: int = 90
    deadline_in_range_bonus: int = 5
    expired_penalty: int = -30
    missing_deadline_penalty: int = -5
    minimum_score_for_alert: int = 75
    closing_soon_days: int = 3


class ScoringFile(BaseModel):
    scoring: ScoringConfig
