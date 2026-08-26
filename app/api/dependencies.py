"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.opportunity import OpportunityRepository
from app.repositories.run import RunRepository
from app.repositories.source import SourceRepository


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def opportunity_repo(
    session: AsyncSession = Depends(db_session),
) -> OpportunityRepository:
    return OpportunityRepository(session)


async def source_repo(session: AsyncSession = Depends(db_session)) -> SourceRepository:
    return SourceRepository(session)


async def run_repo(session: AsyncSession = Depends(db_session)) -> RunRepository:
    return RunRepository(session)
