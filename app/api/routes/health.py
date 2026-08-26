"""Health, readiness and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.api.dependencies import db_session, opportunity_repo, run_repo, source_repo
from app.core.config import get_settings
from app.core.enums import DeadlineStatus, ScoreRating, SourceHealthStatus
from app.repositories.opportunity import OpportunityRepository
from app.repositories.run import RunRepository
from app.repositories.source import SourceRepository
from app.schemas.api import HealthResponse, MetricsSummary, ReadyResponse
from app.services.normalisation.dates import ensure_utc, utcnow

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns process liveness without touching the database.",
)
async def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", version=__version__, environment=settings.app_env)


@router.get(
    "/health/ready",
    response_model=ReadyResponse,
    summary="Readiness probe",
    description="Confirms the application can reach its configured database.",
)
async def ready(session: AsyncSession = Depends(db_session)) -> ReadyResponse:
    await session.execute(text("SELECT 1"))
    return ReadyResponse(status="ok", database="ok")


@router.get(
    "/metrics/summary",
    response_model=MetricsSummary,
    summary="Dashboard-ready pipeline summary",
)
async def metrics_summary(
    opportunities: OpportunityRepository = Depends(opportunity_repo),
    sources: SourceRepository = Depends(source_repo),
    runs: RunRepository = Depends(run_repo),
) -> MetricsSummary:
    all_sources = await sources.list_all()
    latest = await runs.latest()
    now = utcnow()
    newest = await opportunities.newest(limit=500)
    new_today = len(
        [
            item
            for item in newest
            if item.first_seen_at is not None
            and (now - (ensure_utc(item.first_seen_at) or now)).days < 1
        ]
    )
    return MetricsSummary(
        total_opportunities=await opportunities.count(),
        new_opportunities=new_today,
        high_priority=await opportunities.count_rating(ScoreRating.HIGH)
        + await opportunities.count_rating(ScoreRating.VERY_HIGH),
        closing_soon=await opportunities.count_deadline(DeadlineStatus.CRITICAL)
        + await opportunities.count_deadline(DeadlineStatus.URGENT),
        expired=await opportunities.count_deadline(DeadlineStatus.EXPIRED),
        sources_healthy=len(
            [s for s in all_sources if s.health_status == SourceHealthStatus.HEALTHY]
        ),
        sources_degraded=len(
            [s for s in all_sources if s.health_status == SourceHealthStatus.DEGRADED]
        ),
        sources_unhealthy=len(
            [s for s in all_sources if s.health_status == SourceHealthStatus.UNHEALTHY]
        ),
        last_run_id=latest.id if latest else None,
        last_run_status=latest.status if latest else None,
        last_run_duration_ms=latest.duration_ms if latest else None,
        last_run_metrics=latest.metrics if latest else {},
    )
