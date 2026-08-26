"""Prefect 3 wrappers around the in-process pipeline.

The CLI demo does not require a Prefect server. These flows exist so the same
pipeline can be scheduled in environments that already run Prefect.
"""

from __future__ import annotations

from prefect import flow, task

from app.core.enums import RunTrigger
from app.db.session import get_session_factory
from app.services.pipeline import OpportunityPipeline
from app.sources.registry import enabled_sources


@task(name="load-enabled-sources", retries=0)
async def load_enabled_sources(source: str | None = None) -> list[str]:
    return [name for name, _config, _connector in enabled_sources(only=source)]


@task(name="run-opportunity-pipeline", retries=1, retry_delay_seconds=5)
async def run_pipeline_task(source: str | None = None) -> dict[str, object]:
    factory = get_session_factory()
    async with factory() as session:
        result = await OpportunityPipeline(session).run(
            source_name=source, trigger=RunTrigger.SCHEDULE
        )
        await session.commit()
    return {"run_id": str(result.run_id), "status": result.status, **result.metrics.as_dict()}


@flow(name="opportunity-intelligence-pipeline", log_prints=True)
async def opportunity_pipeline(source: str | None = None) -> dict[str, object]:
    names = await load_enabled_sources(source)
    print(f"Enabled sources: {', '.join(names)}")
    return await run_pipeline_task(source)
