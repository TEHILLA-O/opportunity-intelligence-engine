"""Opportunity query API."""

from __future__ import annotations

from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import opportunity_repo
from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.repositories.opportunity import OpportunityRepository
from app.schemas.api import OpportunityDetail, OpportunityFilters, OpportunityListItem, Page

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _filters(
    min_score: int | None = Query(default=None, ge=0, le=100),
    max_score: int | None = Query(default=None, ge=0, le=100),
    source: str | None = None,
    organisation: str | None = None,
    keyword: str | None = None,
    category: str | None = None,
    status: str | None = None,
    rating: str | None = None,
    deadline_status: str | None = None,
) -> OpportunityFilters:
    return OpportunityFilters(
        min_score=min_score,
        max_score=max_score,
        source=source,
        organisation=organisation,
        keyword=keyword,
        category=category,
        status=status,
        rating=rating,
        deadline_status=deadline_status,
    )


@router.get(
    "",
    response_model=Page[OpportunityListItem],
    summary="List opportunities",
    description="Paginated, filterable list of normalised opportunities ordered by score by default.",
)
async def list_opportunities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    sort: str = "score",
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    filters: OpportunityFilters = Depends(_filters),
    repo: OpportunityRepository = Depends(opportunity_repo),
) -> Page[OpportunityListItem]:
    items, total = await repo.list_filtered(
        filters,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order,
        source_name=filters.source,
    )
    return Page(
        items=[OpportunityListItem.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
        pages=ceil(total / page_size) if page_size else 0,
    )


@router.get(
    "/top", response_model=list[OpportunityListItem], summary="Highest scoring opportunities"
)
async def top(
    limit: int = Query(default=20, ge=1, le=100),
    repo: OpportunityRepository = Depends(opportunity_repo),
) -> list[OpportunityListItem]:
    items = await repo.high_priority(limit=limit)
    return [OpportunityListItem.model_validate(item) for item in items]


@router.get(
    "/closing-soon", response_model=list[OpportunityListItem], summary="Deadlines closing soon"
)
async def closing_soon(
    limit: int = Query(default=20, ge=1, le=100),
    repo: OpportunityRepository = Depends(opportunity_repo),
) -> list[OpportunityListItem]:
    items = await repo.closing_soon(limit=limit)
    return [OpportunityListItem.model_validate(item) for item in items]


@router.get("/new", response_model=list[OpportunityListItem], summary="Most recently discovered")
async def newest(
    limit: int = Query(default=20, ge=1, le=100),
    repo: OpportunityRepository = Depends(opportunity_repo),
) -> list[OpportunityListItem]:
    items = await repo.newest(limit=limit)
    return [OpportunityListItem.model_validate(item) for item in items]


@router.get("/{opportunity_id}", response_model=OpportunityDetail, summary="Opportunity detail")
async def get_opportunity(
    opportunity_id: UUID,
    repo: OpportunityRepository = Depends(opportunity_repo),
) -> OpportunityDetail:
    item = await repo.get(opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityDetail.model_validate(item)
