"""Automation run history and on-demand execution."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import db_session, run_repo
from app.core.enums import RunTrigger
from app.repositories.run import RunRepository
from app.schemas.api import RunCreate, RunRead
from app.services.pipeline import OpportunityPipeline

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunRead], summary="Recent automation runs")
async def list_runs(limit: int = 20, repo: RunRepository = Depends(run_repo)) -> list[RunRead]:
    return [RunRead.model_validate(item) for item in await repo.list_recent(limit=limit)]


@router.get("/{run_id}", response_model=RunRead, summary="Run detail including stage timings")
async def get_run(run_id: UUID, repo: RunRepository = Depends(run_repo)) -> RunRead:
    item = await repo.get(run_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunRead.model_validate(item)


@router.post("", response_model=RunRead, summary="Trigger a pipeline run")
async def create_run(
    payload: RunCreate,
    session: AsyncSession = Depends(db_session),
) -> RunRead:
    pipeline = OpportunityPipeline(session)
    result = await pipeline.run(
        source_name=payload.source,
        trigger=payload.trigger or RunTrigger.API,
        generate_export=True,
        notify=True,
    )
    repo = RunRepository(session)
    run = await repo.get(result.run_id)
    if run is None:
        raise HTTPException(status_code=500, detail="Run record missing after execution")
    return RunRead.model_validate(run)
