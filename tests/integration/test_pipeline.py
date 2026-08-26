"""Pipeline idempotency, change detection and rollback tests."""

from __future__ import annotations

import pytest
from app.core.enums import RunTrigger
from app.db.models.opportunity import Opportunity, OpportunityHistory
from app.db.models.run import IngestionError
from app.services.pipeline import OpportunityPipeline
from app.sources.demo_dataset import write_demo_files
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_pipeline_idempotent_on_second_run(db_session: AsyncSession) -> None:
    write_demo_files()
    pipeline = OpportunityPipeline(db_session)
    first = await pipeline.run(
        source_name="demo", trigger=RunTrigger.TEST, generate_export=False, notify=False
    )
    await db_session.commit()
    count_after_first = (await db_session.execute(select(Opportunity))).scalars().all()
    second = await pipeline.run(
        source_name="demo", trigger=RunTrigger.TEST, generate_export=False, notify=False
    )
    await db_session.commit()
    count_after_second = (await db_session.execute(select(Opportunity))).scalars().all()
    assert first.metrics.new_records > 0
    assert len(count_after_first) == len(count_after_second)
    assert second.metrics.new_records == 0
    assert second.metrics.duplicates >= first.metrics.new_records


@pytest.mark.asyncio
async def test_pipeline_detects_updates(db_session: AsyncSession) -> None:
    write_demo_files()
    pipeline = OpportunityPipeline(db_session)
    await pipeline.run(
        source_name="demo", trigger=RunTrigger.TEST, generate_export=False, notify=False
    )
    await db_session.commit()
    updated = await pipeline.run(
        source_name="demo",
        trigger=RunTrigger.TEST,
        mutate_demo=True,
        generate_export=False,
        notify=False,
    )
    await db_session.commit()
    history = (await db_session.execute(select(OpportunityHistory))).scalars().all()
    assert updated.metrics.updated_records >= 1
    assert history


@pytest.mark.asyncio
async def test_invalid_records_are_stored_not_silently_dropped(db_session: AsyncSession) -> None:
    write_demo_files()
    pipeline = OpportunityPipeline(db_session)
    await pipeline.run(
        source_name="demo", trigger=RunTrigger.TEST, generate_export=False, notify=False
    )
    await db_session.commit()
    errors = (await db_session.execute(select(IngestionError))).scalars().all()
    assert errors
    assert any("title" in err.error_message.lower() for err in errors)


@pytest.mark.asyncio
async def test_database_rollback_on_catastrophic_failure(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_demo_files()
    pipeline = OpportunityPipeline(db_session)

    async def boom(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("simulated persistence failure")

    # Per-record errors are isolated. A failure after the batch (source health write)
    # is treated as catastrophic and must roll back uncommitted opportunity rows.
    monkeypatch.setattr(pipeline.sources, "record_success", boom)
    with pytest.raises(RuntimeError):
        await pipeline.run(
            source_name="demo", trigger=RunTrigger.TEST, generate_export=False, notify=False
        )
    remaining = (await db_session.execute(select(Opportunity))).scalars().all()
    assert remaining == []
