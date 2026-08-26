"""Lightweight pipeline benchmark.

Usage:
    uv run python scripts/benchmark_pipeline.py --records 200
"""

from __future__ import annotations

import argparse
import asyncio
import time

from app.core.config import get_settings
from app.db.base_class import Base
from app.db.session import dispose_engine, get_engine, get_session_factory, init_engine
from app.services.pipeline import OpportunityPipeline


async def main(records: int) -> None:
    settings = get_settings()
    settings.ensure_data_dirs()
    await init_engine(settings)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    started = time.perf_counter()
    factory = get_session_factory()
    async with factory() as session:
        result = await OpportunityPipeline(session).run(
            source_name="demo", generate_export=False, notify=False
        )
        await session.commit()
    elapsed = time.perf_counter() - started
    discovered = result.metrics.records_discovered or 1
    print("Opportunity Engine benchmark")
    print(f"requested_hint     {records}")
    print(f"discovered         {result.metrics.records_discovered}")
    print(f"new                {result.metrics.new_records}")
    print(f"duplicates         {result.metrics.duplicates}")
    print(f"wall_clock_seconds {elapsed:.4f}")
    print(f"records_per_second {discovered / elapsed:.2f}")
    print(f"pipeline_seconds   {result.metrics.duration_seconds:.4f}")
    await dispose_engine()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=200)
    args = parser.parse_args()
    asyncio.run(main(args.records))
