"""Server-rendered monitoring dashboard."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session
from app.core.enums import DeadlineStatus, ScoreRating, SourceHealthStatus
from app.repositories.opportunity import OpportunityRepository
from app.repositories.run import RunRepository
from app.repositories.source import SourceRepository
from app.services.normalisation.dates import ensure_utc, utcnow

router = APIRouter(tags=["dashboard"])


@router.get("/", response_class=HTMLResponse, summary="Operations dashboard")
async def dashboard_home(
    request: Request, session: AsyncSession = Depends(db_session)
) -> HTMLResponse:
    opportunities = OpportunityRepository(session)
    sources = SourceRepository(session)
    runs = RunRepository(session)
    all_sources = await sources.list_all()
    latest = await runs.latest()
    top = await opportunities.high_priority(limit=10)
    newest = await opportunities.newest(limit=8)
    closing = await opportunities.closing_soon(limit=8)
    recent_runs = await runs.list_recent(limit=8)
    stats = {
        "total": await opportunities.count(),
        "high": await opportunities.count_rating(ScoreRating.HIGH)
        + await opportunities.count_rating(ScoreRating.VERY_HIGH),
        "closing": await opportunities.count_deadline(DeadlineStatus.CRITICAL)
        + await opportunities.count_deadline(DeadlineStatus.URGENT),
        "expired": await opportunities.count_deadline(DeadlineStatus.EXPIRED),
        "healthy": len([s for s in all_sources if s.health_status == SourceHealthStatus.HEALTHY]),
        "new": len(newest),
        "duration": f"{(latest.duration_ms or 0) / 1000:.2f}s" if latest else "—",
        "last_status": latest.status if latest else "—",
    }
    return request.app.state.templates.TemplateResponse(
        request,
        "index.html",
        {
            "stats": stats,
            "top": top,
            "newest": newest,
            "closing": closing,
            "sources": all_sources,
            "runs": recent_runs,
            "latest": latest,
        },
    )


@router.get("/opportunities/{opportunity_id}", response_class=HTMLResponse)
async def dashboard_opportunity(
    opportunity_id: UUID, request: Request, session: AsyncSession = Depends(db_session)
) -> HTMLResponse:
    item = await OpportunityRepository(session).get(opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return request.app.state.templates.TemplateResponse(request, "opportunity.html", {"item": item})


@router.get("/runs", response_class=HTMLResponse)
async def dashboard_runs(
    request: Request, session: AsyncSession = Depends(db_session)
) -> HTMLResponse:
    runs = await RunRepository(session).list_recent(limit=30)
    return request.app.state.templates.TemplateResponse(request, "runs.html", {"runs": runs})


@router.get("/metrics", response_class=HTMLResponse, summary="Pipeline metrics dashboard")
async def dashboard_metrics(
    request: Request, session: AsyncSession = Depends(db_session)
) -> HTMLResponse:
    opportunities = OpportunityRepository(session)
    sources = SourceRepository(session)
    runs = RunRepository(session)
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
    metrics = {
        "total_opportunities": await opportunities.count(),
        "new_opportunities": new_today,
        "high_priority": await opportunities.count_rating(ScoreRating.HIGH)
        + await opportunities.count_rating(ScoreRating.VERY_HIGH),
        "closing_soon": await opportunities.count_deadline(DeadlineStatus.CRITICAL)
        + await opportunities.count_deadline(DeadlineStatus.URGENT),
        "expired": await opportunities.count_deadline(DeadlineStatus.EXPIRED),
        "sources_healthy": len(
            [s for s in all_sources if s.health_status == SourceHealthStatus.HEALTHY]
        ),
        "sources_degraded": len(
            [s for s in all_sources if s.health_status == SourceHealthStatus.DEGRADED]
        ),
        "sources_unhealthy": len(
            [s for s in all_sources if s.health_status == SourceHealthStatus.UNHEALTHY]
        ),
        "last_run_id": latest.id if latest else None,
        "last_run_status": latest.status if latest else None,
        "last_run_duration_ms": latest.duration_ms if latest else None,
    }
    raw_metrics = latest.metrics if latest else {}
    skip_keys = {"new_ids", "updated_ids"}
    run_metrics = sorted((k, v) for k, v in raw_metrics.items() if k not in skip_keys)
    return request.app.state.templates.TemplateResponse(
        request,
        "metrics.html",
        {"metrics": metrics, "run_metrics": run_metrics},
    )
