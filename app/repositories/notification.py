"""Notification and export audit repositories."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.export import ExportRecord
from app.db.models.notification import NotificationRecord


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        event_type: str,
        provider: str,
        status: str,
        payload: dict[str, Any],
        opportunity_id: uuid.UUID | None,
        run_id: uuid.UUID | None,
        sent_at: datetime | None,
        error_message: str | None = None,
    ) -> NotificationRecord:
        row = NotificationRecord(
            event_type=event_type,
            provider=provider,
            status=status,
            payload=payload,
            opportunity_id=opportunity_id,
            run_id=run_id,
            sent_at=sent_at,
            error_message=error_message,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_recent(self, *, limit: int = 50) -> Sequence[NotificationRecord]:
        result = await self.session.execute(
            select(NotificationRecord).order_by(NotificationRecord.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


class ExportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        format: str,
        path: str,
        record_count: int,
        run_id: uuid.UUID | None,
        extra: dict[str, Any] | None = None,
    ) -> ExportRecord:
        row = ExportRecord(
            format=format,
            path=path,
            record_count=record_count,
            run_id=run_id,
            extra=extra or {},
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_recent(self, *, limit: int = 20) -> Sequence[ExportRecord]:
        result = await self.session.execute(
            select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
