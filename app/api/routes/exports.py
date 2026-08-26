"""Export generation API."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session
from app.repositories.notification import ExportRepository
from app.repositories.opportunity import OpportunityRepository
from app.schemas.api import ExportCreate, ExportRead
from app.services.reporting.service import ReportingService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("", response_model=ExportRead, summary="Generate an Excel, CSV or JSON export")
async def create_export(
    payload: ExportCreate, session: AsyncSession = Depends(db_session)
) -> ExportRead:
    opportunities = await OpportunityRepository(session).list_all()
    path = ReportingService().export(list(opportunities), payload.format, run_id=payload.run_id)
    record = await ExportRepository(session).create(
        format=payload.format,
        path=str(path),
        record_count=len(opportunities),
        run_id=payload.run_id,
    )
    return ExportRead.model_validate(record)
