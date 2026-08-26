"""Recordable case-study demonstration.

Sequence: reset demo environment, seed, run, re-run (idempotency), mutate (changes),
export, then print API instructions.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.core.enums import RunTrigger
from app.core.logging import configure_logging
from app.db.base_class import Base
from app.db.session import dispose_engine, get_engine, get_session_factory, init_engine
from app.services.pipeline import OpportunityPipeline
from app.sources.demo_dataset import write_demo_files
from rich.console import Console

console = Console()


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.ensure_data_dirs()
    db_file = Path("data/opportunity_engine.db")
    if db_file.exists():
        db_file.unlink()
    write_demo_files()
    await init_engine(settings)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = get_session_factory()
    async with factory() as session:
        pipeline = OpportunityPipeline(session)
        console.rule("1. Collection + normalisation + scoring")
        first = await pipeline.run(trigger=RunTrigger.DEMO, generate_export=True, notify=True)
        await session.commit()
        console.print(first.metrics.as_dict())

        console.rule("2. Idempotent re-run")
        second = await pipeline.run(trigger=RunTrigger.DEMO, generate_export=False, notify=False)
        await session.commit()
        console.print(
            {
                "new_records": second.metrics.new_records,
                "duplicates": second.metrics.duplicates,
                "updated_records": second.metrics.updated_records,
            }
        )

        console.rule("3. Change detection")
        third = await pipeline.run(
            trigger=RunTrigger.DEMO, mutate_demo=True, generate_export=True, notify=True
        )
        await session.commit()
        console.print(
            {
                "updated_records": third.metrics.updated_records,
                "export_path": third.metrics.export_path,
            }
        )

    console.rule("Next steps")
    console.print("uv run opportunity-engine api")
    console.print("Dashboard: http://127.0.0.1:8000/")
    console.print("OpenAPI:   http://127.0.0.1:8000/docs")
    await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
