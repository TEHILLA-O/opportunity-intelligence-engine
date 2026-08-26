"""Command-line interface."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from app.core.config import get_settings
from app.core.enums import ExportFormat, RunTrigger
from app.core.logging import configure_logging
from app.db.session import get_session_factory
from app.repositories.opportunity import OpportunityRepository
from app.repositories.run import RunRepository
from app.repositories.source import SourceRepository
from app.services.pipeline import OpportunityPipeline
from app.services.reporting.service import ReportingService
from app.sources.demo_dataset import write_demo_files
from app.sources.registry import enabled_sources, load_sources_file

app = typer.Typer(
    name="opportunity-engine",
    help="Opportunity Intelligence Automation Engine",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _configure() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.ensure_data_dirs()


async def _with_pipeline(action):  # type: ignore[no-untyped-def]
    _configure()
    factory = get_session_factory()
    async with factory() as session:
        pipeline = OpportunityPipeline(session)
        result = await action(pipeline)
        await session.commit()
        return result


@app.command()
def run(
    source: str | None = typer.Option(None, help="Limit the run to a single configured source."),
    mutate: bool = typer.Option(
        False, help="Apply demo mutations to demonstrate change detection."
    ),
) -> None:
    """Execute the opportunity collection pipeline."""

    async def _run() -> None:
        result = await _with_pipeline(
            lambda pipeline: pipeline.run(
                source_name=source, trigger=RunTrigger.CLI, mutate_demo=mutate
            )
        )
        console.print(f"[bold green]Run {result.run_id}[/] {result.status}")
        console.print(result.metrics.as_dict())

    asyncio.run(_run())


@app.command()
def demo(
    apply_updates: bool = typer.Option(
        False, help="Re-run using mutated demo records to show change detection."
    ),
) -> None:
    """Complete local demonstration using bundled sample data only."""

    async def _demo() -> None:
        _configure()
        write_demo_files()
        factory = get_session_factory()
        async with factory() as session:
            from app.db.base_class import Base
            from app.db.session import get_engine

            engine = get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            pipeline = OpportunityPipeline(session)
            result = await pipeline.run(
                trigger=RunTrigger.DEMO,
                mutate_demo=apply_updates,
                generate_export=True,
                notify=True,
            )
            await session.commit()
        metrics = result.metrics.as_dict()
        console.rule("Opportunity Engine demo")
        console.print(f"Run ID     {result.run_id}")
        console.print(f"Status     {result.status}")
        console.print(f"Discovered {metrics['records_discovered']}")
        console.print(f"New        {metrics['new_records']}")
        console.print(f"Updated    {metrics['updated_records']}")
        console.print(f"Duplicates {metrics['duplicates']}")
        console.print(f"Invalid    {metrics['invalid_records']}")
        console.print(f"Duration   {metrics['duration_seconds']}s")
        if metrics.get("export_path"):
            console.print(f"Excel      {metrics['export_path']}")
        console.print("\nNext: uv run opportunity-engine api   then open http://127.0.0.1:8000/")

    asyncio.run(_demo())


@app.command()
def sources() -> None:
    """List configured sources."""

    _configure()
    file = load_sources_file()
    table = Table(title="Configured sources")
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Enabled")
    table.add_column("Locator")
    for name, config in file.sources.items():
        table.add_row(
            name, config.type, str(config.enabled), config.url or config.path or "bundled"
        )
    console.print(table)


@app.command()
def health() -> None:
    """Probe configured sources without persisting records."""

    async def _health() -> None:
        _configure()
        table = Table(title="Source health")
        table.add_column("Name")
        table.add_column("Healthy")
        table.add_column("Message")
        for name, _config, connector in enabled_sources():
            result = await connector.healthcheck()
            table.add_row(name, str(result.healthy), result.message)
        console.print(table)

    asyncio.run(_health())


@app.command("export")
def export_cmd(
    format: ExportFormat = typer.Option(ExportFormat.XLSX, "--format"),
) -> None:
    """Export stored opportunities to Excel, CSV or JSON."""

    async def _export() -> None:
        _configure()
        factory = get_session_factory()
        async with factory() as session:
            items = await OpportunityRepository(session).list_all()
            path = ReportingService().export(list(items), format)
            console.print(f"Wrote {path}")

    asyncio.run(_export())


@app.command()
def opportunities(
    top: int = typer.Option(20, help="Number of highest-scoring rows to display."),
) -> None:
    """Show top stored opportunities."""

    async def _list() -> None:
        _configure()
        factory = get_session_factory()
        async with factory() as session:
            items = await OpportunityRepository(session).high_priority(limit=top)
            table = Table(title=f"Top {top} opportunities")
            table.add_column("Score")
            table.add_column("Title")
            table.add_column("Organisation")
            table.add_column("Deadline")
            for item in items:
                table.add_row(
                    str(item.score),
                    item.title[:60],
                    item.organisation or "—",
                    item.deadline_at.strftime("%Y-%m-%d") if item.deadline_at else "—",
                )
            console.print(table)

    asyncio.run(_list())


@app.command()
def metrics() -> None:
    """Print a compact operations summary."""

    async def _metrics() -> None:
        _configure()
        factory = get_session_factory()
        async with factory() as session:
            run = await RunRepository(session).latest()
            sources_repo = SourceRepository(session)
            all_sources = await sources_repo.list_all()
            opps = OpportunityRepository(session)
            console.rule("Opportunity Engine")
            console.print("[bold]Last run[/]")
            if run:
                console.print(f"Run ID:           {run.id}")
                console.print(f"Status:           {run.status}")
                console.print(f"Duration:         {(run.duration_ms or 0) / 1000:.2f}s")
                m = run.metrics or {}
                console.print("\n[bold]Pipeline[/]")
                console.print(f"Discovered:       {m.get('records_discovered', 0)}")
                console.print(f"New:              {m.get('new_records', 0)}")
                console.print(f"Updated:          {m.get('updated_records', 0)}")
                console.print(f"Duplicates:       {m.get('duplicates', 0)}")
                console.print(f"Invalid:          {m.get('invalid_records', 0)}")
            from app.core.enums import ScoreRating, SourceHealthStatus

            console.print("\n[bold]Priority[/]")
            for rating in ScoreRating:
                count = await opps.count_rating(rating)
                console.print(f"{rating.value.replace('_', ' ').title():<16} {count}")
            console.print("\n[bold]Sources[/]")
            healthy = len([s for s in all_sources if s.health_status == SourceHealthStatus.HEALTHY])
            degraded = len(
                [s for s in all_sources if s.health_status == SourceHealthStatus.DEGRADED]
            )
            failed = len(
                [s for s in all_sources if s.health_status == SourceHealthStatus.UNHEALTHY]
            )
            console.print(f"Healthy:          {healthy}")
            console.print(f"Degraded:         {degraded}")
            console.print(f"Failed:           {failed}")

    asyncio.run(_metrics())


db_app = typer.Typer(help="Database helpers")
app.add_typer(db_app, name="db")


@db_app.command("upgrade")
def db_upgrade() -> None:
    """Apply Alembic migrations (or create schema for a fresh SQLite demo)."""

    async def _upgrade() -> None:
        _configure()
        from alembic import command
        from alembic.config import Config

        from app.core.config import PROJECT_ROOT
        from app.db.base_class import Base
        from app.db.session import get_engine

        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
        try:
            command.upgrade(cfg, "head")
        except Exception:
            console.print(
                "Alembic upgrade skipped or already applied; SQLAlchemy metadata ensured."
            )
        console.print("Database schema is ready.")

    asyncio.run(_upgrade())


@app.command()
def api(
    host: str | None = None,
    port: int | None = None,
) -> None:
    """Start the FastAPI server."""

    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=settings.app_debug,
    )


if __name__ == "__main__":
    app()
