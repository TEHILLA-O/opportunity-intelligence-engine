"""One-shot database bootstrap for serverless deployments (e.g. Vercel)."""

from __future__ import annotations

import os

import structlog

from app.core.config import get_settings, sqlite_database_url
from app.core.enums import RunTrigger
from app.db.base_class import Base
from app.db.session import get_engine, get_session_factory, init_engine
from app.repositories.opportunity import OpportunityRepository
from app.services.pipeline import OpportunityPipeline
from app.sources.demo_dataset import write_demo_files

logger = structlog.get_logger(__name__)
_bootstrapped = False
_bootstrap_error: str | None = None


def is_serverless() -> bool:
    return bool(os.environ.get("VERCEL"))


def bootstrap_error() -> str | None:
    return _bootstrap_error


def is_bootstrapped() -> bool:
    return _bootstrapped


async def ensure_serverless_ready() -> None:
    """Create schema and seed demo data on cold start when running on Vercel."""
    global _bootstrapped, _bootstrap_error
    if _bootstrapped or not is_serverless():
        return
    if _bootstrap_error is not None:
        return

    try:
        settings = get_settings()
        settings.ensure_data_dirs()
        await init_engine(settings)

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory = get_session_factory()
        async with factory() as session:
            count = await OpportunityRepository(session).count()
            if count == 0:
                logger.info("serverless_seeding_demo")
                write_demo_files()
                pipeline = OpportunityPipeline(session)
                await pipeline.run(
                    source_name="demo",
                    trigger=RunTrigger.CLI,
                    generate_export=False,
                    notify=False,
                )
                await session.commit()

        _bootstrapped = True
        logger.info("serverless_bootstrap_complete")
    except Exception as exc:  # noqa: BLE001
        _bootstrap_error = str(exc)
        logger.exception("serverless_bootstrap_failed", error=str(exc))
