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
