"""One-shot database bootstrap for serverless deployments (e.g. Vercel)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import structlog

from app.core.config import PROJECT_ROOT, get_settings
from app.db.session import get_engine, init_engine

logger = structlog.get_logger(__name__)
_bootstrapped = False
_bootstrap_error: str | None = None

SEED_DB = PROJECT_ROOT / "data" / "demo" / "opportunity_engine_seed.db"


def is_serverless() -> bool:
    return bool(os.environ.get("VERCEL"))


def bootstrap_error() -> str | None:
    return _bootstrap_error


def is_bootstrapped() -> bool:
    return _bootstrapped


def _database_file(settings_database_url: str) -> Path:
    prefix = "sqlite+aiosqlite:///"
    if settings_database_url.startswith(prefix):
        return Path(settings_database_url.removeprefix(prefix))
    return Path("/tmp/opportunity-engine/opportunity_engine.db")


async def ensure_serverless_ready() -> None:
    """Copy bundled demo SQLite to /tmp on cold start (fast, no pipeline run)."""
    global _bootstrapped, _bootstrap_error
    if _bootstrapped or not is_serverless():
        return
    if _bootstrap_error is not None:
        return

    try:
        settings = get_settings()
        settings.ensure_data_dirs()
        db_file = _database_file(settings.database_url)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        if not db_file.exists():
            if SEED_DB.exists():
                shutil.copy2(SEED_DB, db_file)
                logger.info("serverless_seed_db_copied", target=str(db_file))
            else:
                msg = f"Seed database missing at {SEED_DB}"
                raise FileNotFoundError(msg)

        await init_engine(settings)
        get_engine()
        _bootstrapped = True
        logger.info("serverless_bootstrap_complete")
    except Exception as exc:  # noqa: BLE001
        _bootstrap_error = str(exc)
        logger.exception("serverless_bootstrap_failed", error=str(exc))
