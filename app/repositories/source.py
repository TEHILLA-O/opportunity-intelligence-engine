"""Source persistence and health updates."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SourceHealthStatus
from app.db.models.source import Source


class SourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> Sequence[Source]:
        result = await self.session.execute(select(Source).order_by(Source.name))
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Source | None:
        result = await self.session.execute(select(Source).where(Source.name == name))
        return result.scalar_one_or_none()

    async def get(self, source_id: uuid.UUID) -> Source | None:
        return await self.session.get(Source, source_id)

    async def upsert(
        self,
        *,
        name: str,
        source_type: str,
        enabled: bool,
        description: str | None,
        config: dict[str, Any],
    ) -> Source:
        existing = await self.get_by_name(name)
        if existing is None:
            existing = Source(
                name=name,
                source_type=source_type,
                enabled=enabled,
                description=description,
                config=config,
            )
            self.session.add(existing)
        else:
            existing.source_type = source_type
            existing.enabled = enabled
            existing.description = description
            existing.config = config
        await self.session.flush()
        return existing

    async def record_success(
        self,
        source: Source,
        *,
        now: datetime,
        duration_ms: float,
        http_status: int | None,
        discovered: int,
        accepted: int,
        rejected: int,
    ) -> None:
        source.last_successful_run_at = now
        source.consecutive_failures = 0
        source.last_http_status = http_status
        source.records_discovered += discovered
        source.records_accepted += accepted
        source.records_rejected += rejected
        if source.avg_response_ms is None:
            source.avg_response_ms = duration_ms
        else:
            source.avg_response_ms = (source.avg_response_ms * 0.7) + (duration_ms * 0.3)
        source.health_status = SourceHealthStatus.HEALTHY
        await self.session.flush()

    async def record_failure(
        self,
        source: Source,
        *,
        now: datetime,
        http_status: int | None,
        duration_ms: float | None = None,
    ) -> None:
        source.last_failed_run_at = now
        source.consecutive_failures += 1
        source.last_http_status = http_status
        if duration_ms is not None:
            if source.avg_response_ms is None:
                source.avg_response_ms = duration_ms
            else:
                source.avg_response_ms = (source.avg_response_ms * 0.7) + (duration_ms * 0.3)
        if source.consecutive_failures >= 3:
            source.health_status = SourceHealthStatus.UNHEALTHY
        else:
            source.health_status = SourceHealthStatus.DEGRADED
        await self.session.flush()
