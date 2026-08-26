"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api.error_handlers import register_error_handlers
from app.api.routes import exports, health, opportunities, runs, sources
from app.bootstrap import ensure_serverless_ready, is_bootstrapped, is_serverless
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.dashboard.routes import router as dashboard_router
from app.db.session import dispose_engine, get_engine

OPENAPI_TAGS = [
    {"name": "health", "description": "Liveness, readiness and pipeline summary metrics."},
    {"name": "opportunities", "description": "Query normalised, scored commercial opportunities."},
    {"name": "sources", "description": "Configured connectors and source health."},
    {"name": "runs", "description": "Automation run history and on-demand execution."},
    {"name": "exports", "description": "Generate Excel, CSV or JSON reports."},
    {"name": "dashboard", "description": "Server-rendered monitoring dashboard."},
]


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level, json_output=settings.app_env == "production")
    logger = get_logger(__name__)
    try:
        settings.ensure_data_dirs()
        if is_serverless():
            await ensure_serverless_ready()
        else:
            get_engine()
    except Exception:
        logger.exception("startup_initialisation_failed")
    yield
    try:
        await dispose_engine()
    except Exception:
        logger.exception("engine_dispose_failed")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="Opportunity Intelligence Automation Engine",
        version=__version__,
        description=(
            "Collect, normalise, deduplicate, score and report commercial opportunities "
            "from multiple sources. The deterministic Python pipeline does not require an LLM."
        ),
        openapi_tags=OPENAPI_TAGS,
        contact={"name": "Opportunity Engine", "url": "https://github.com/"},
        license_info={"name": "MIT"},
        lifespan=lifespan,
    )
    register_error_handlers(application)

    @application.middleware("http")
    async def _serverless_bootstrap(request: Request, call_next):  # type: ignore[no-untyped-def]
        if is_serverless() and not is_bootstrapped():
            await ensure_serverless_ready()
        return await call_next(request)

    application.include_router(health.router)
    application.include_router(opportunities.router, prefix="/api/v1")
    application.include_router(sources.router, prefix="/api/v1")
    application.include_router(runs.router, prefix="/api/v1")
    application.include_router(exports.router, prefix="/api/v1")
    application.include_router(dashboard_router)

    static_dir = Path(__file__).resolve().parent / "dashboard" / "static"
    if static_dir.exists():
        application.mount("/static", StaticFiles(directory=static_dir), name="static")

    templates = Jinja2Templates(
        directory=str(Path(__file__).resolve().parent / "dashboard" / "templates")
    )
    application.state.templates = templates
    application.state.settings = settings
    return application


app = create_app()
