"""Repository behaviour tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.core.enums import SourceType
from app.repositories.source import SourceRepository
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_source_upsert(db_session: AsyncSession) -> None:
    repo = SourceRepository(db_session)
    first = await repo.upsert(
        name="demo",
        source_type=SourceType.MOCK,
        enabled=True,
        description="Demo",
        config={},
    )
    second = await repo.upsert(
        name="demo",
        source_type=SourceType.MOCK,
        enabled=True,
        description="Demo updated",
        config={"k": "v"},
    )
    assert first.id == second.id
    assert second.description == "Demo updated"
    await repo.record_success(
        second,
        now=datetime.now(UTC),
        duration_ms=12.0,
        http_status=200,
        discovered=10,
        accepted=9,
        rejected=1,
    )
    assert second.health_status == "healthy"
    await repo.record_failure(second, now=datetime.now(UTC), http_status=500)
    assert second.consecutive_failures == 1
    assert second.health_status == "degraded"
