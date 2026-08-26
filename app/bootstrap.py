"""One-shot database bootstrap for serverless deployments (e.g. Vercel)."""

from __future__ import annotations

import os

import structlog
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import PROJECT_ROOT, get_settings
from app.core.enums import RunTrigger
from app.db.base_class import Base
from app.db.session import get_engine, get_session_factory
from app.repositories.opportunity import OpportunityRepository
from app.services.pipeline import OpportunityPipeline
from app.sources.demo_dataset import write_demo_files

logger = structlog.get_logger(__name__)
_bootstrapped = False


def is_serverless() -> bool:
    return bool(os.environ.get("VERCEL"))


async def ensure_serverless_ready() -> None:
    """Create schema and seed demo data on cold start when running on Vercel."""
    global _bootstrapped
    if _bootstrapped or not is_serverless():
        return

    settings = get_settings()
    settings.ensure_data_dirs()
    engine = get_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    try:
        command.upgrade(cfg, "head")
    except Exception as exc:  # noqa: BLE001
        logger.warning("alembic_upgrade_skipped", error=str(exc))

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


async def warm_session(session: AsyncSession) -> None:
    """No-op helper kept for tests."""
    _ = session
