"""Source registry API."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import source_repo
from app.repositories.source import SourceRepository
from app.schemas.api import SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceRead], summary="List configured sources")
async def list_sources(repo: SourceRepository = Depends(source_repo)) -> list[SourceRead]:
    return [SourceRead.model_validate(item) for item in await repo.list_all()]


@router.get("/{source_id}", response_model=SourceRead, summary="Source health and counters")
async def get_source(source_id: UUID, repo: SourceRepository = Depends(source_repo)) -> SourceRead:
    item = await repo.get(source_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceRead.model_validate(item)
