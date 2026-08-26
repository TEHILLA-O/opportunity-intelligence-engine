"""Automation run and ingestion error persistence."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import RunStatus, StepStatus
from app.db.models.run import AutomationRun, AutomationRunStep, IngestionError


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, trigger: str, source_filter: str | None = None) -> AutomationRun:
        run = AutomationRun(trigger=trigger, source_filter=source_filter, status=RunStatus.PENDING)
        self.session.add(run)
        await self.session.flush()
        return run

    async def start(self, run: AutomationRun, *, now: datetime) -> None:
        run.status = RunStatus.RUNNING
        run.started_at = now
        await self.session.flush()

    async def finish(
        self,
        run: AutomationRun,
        *,
        status: RunStatus,
        now: datetime,
        metrics: dict[str, Any],
        error_message: str | None = None,
    ) -> None:
        run.status = status
        run.finished_at = now
        run.metrics = metrics
        run.error_message = error_message
        if run.started_at:
            run.duration_ms = int((now - run.started_at).total_seconds() * 1000)
        await self.session.flush()

    async def add_step(
        self,
        run: AutomationRun,
        *,
        name: str,
        status: StepStatus,
        started_at: datetime,
        finished_at: datetime,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> AutomationRunStep:
        step = AutomationRunStep(
            run_id=run.id,
            name=name,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=int((finished_at - started_at).total_seconds() * 1000),
            details=details or {},
            error_message=error_message,
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def add_error(
        self,
        *,
        run_id: uuid.UUID | None,
        source_id: uuid.UUID | None,
        external_id: str | None,
        error_type: str,
        error_message: str,
        raw_payload: dict[str, Any] | None,
    ) -> IngestionError:
        row = IngestionError(
            run_id=run_id,
            source_id=source_id,
            external_id=external_id,
            error_type=error_type,
            error_message=error_message,
            raw_payload=raw_payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(self, run_id: uuid.UUID) -> AutomationRun | None:
        result = await self.session.execute(
            select(AutomationRun)
            .options(selectinload(AutomationRun.steps))
            .where(AutomationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_recent(self, *, limit: int = 20) -> Sequence[AutomationRun]:
        result = await self.session.execute(
            select(AutomationRun)
            .options(selectinload(AutomationRun.steps))
            .order_by(AutomationRun.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def latest(self) -> AutomationRun | None:
        result = await self.session.execute(
            select(AutomationRun)
            .options(selectinload(AutomationRun.steps))
            .order_by(AutomationRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
