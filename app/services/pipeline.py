"""End-to-end automation pipeline.

Transaction strategy
--------------------
- Run and source rows are flushed as the workflow progresses.
- Each incoming record is processed independently. A validation failure writes
  an ingestion_errors row and continues; it does not roll back the source batch.
- Identity matches update in place (idempotent). Confirmed duplicates never
  insert a second opportunity row.
- The session is committed at the end of a successful (or partial) run. A
  catastrophic database error rolls the whole unit of work back.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import DuplicateStatus, RunStatus, RunTrigger, StepStatus
from app.core.exceptions import RecordValidationError
from app.core.logging import bind_run_context, clear_run_context, get_logger
from app.db.models.opportunity import Opportunity
from app.db.models.source import Source
from app.repositories.notification import ExportRepository, NotificationRepository
from app.repositories.opportunity import OpportunityRepository
from app.repositories.run import RunRepository
from app.repositories.source import SourceRepository
from app.schemas.opportunity import NormalisedOpportunity, ScoredOpportunity
from app.schemas.raw import RawOpportunityIn
from app.services.change_detection.engine import ChangeDetectionEngine
from app.services.deduplication.engine import DeduplicationEngine
from app.services.deduplication.fingerprint import content_hash_from_raw
from app.services.normalisation.dates import utcnow
from app.services.normalisation.engine import NormalisationEngine
from app.services.notification.dispatcher import NotificationDispatcher
from app.services.reporting.service import ReportingService
from app.services.scoring.engine import ScoringEngine
from app.services.validation.engine import ValidationEngine
from app.sources.registry import enabled_sources

logger = get_logger(__name__)

PIPELINE_STEPS = (
    "collection",
    "extraction",
    "validation",
    "normalisation",
    "deduplication",
    "scoring",
    "persistence",
    "reporting",
    "notification",
)


@dataclass
class PipelineMetrics:
    sources_attempted: int = 0
    sources_successful: int = 0
    sources_failed: int = 0
    records_discovered: int = 0
    new_records: int = 0
    updated_records: int = 0
    duplicates: int = 0
    ambiguous_duplicates: int = 0
    invalid_records: int = 0
    high_priority_opportunities: int = 0
    duration_seconds: float = 0.0
    export_path: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "sources_attempted": self.sources_attempted,
            "sources_successful": self.sources_successful,
            "sources_failed": self.sources_failed,
            "records_discovered": self.records_discovered,
            "new_records": self.new_records,
            "updated_records": self.updated_records,
            "duplicates": self.duplicates,
            "ambiguous_duplicates": self.ambiguous_duplicates,
            "invalid_records": self.invalid_records,
            "high_priority_opportunities": self.high_priority_opportunities,
            "duration_seconds": round(self.duration_seconds, 4),
            "export_path": self.export_path,
        }


@dataclass
class PipelineResult:
    run_id: uuid.UUID
    status: RunStatus
    metrics: PipelineMetrics
    steps: dict[str, str] = field(default_factory=dict)


class OpportunityPipeline:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.sources = SourceRepository(session)
        self.opportunities = OpportunityRepository(session)
        self.runs = RunRepository(session)
        self.notifications = NotificationRepository(session)
        self.exports = ExportRepository(session)
        self.validator = ValidationEngine()
        self.normaliser = NormalisationEngine()
        self.deduper = DeduplicationEngine()
        self.changes = ChangeDetectionEngine()
        self.scorer = ScoringEngine()
        self.reporter = ReportingService()
        self.notifier = NotificationDispatcher(session)

    async def run(
        self,
        *,
        source_name: str | None = None,
        trigger: str = RunTrigger.CLI,
        mutate_demo: bool = False,
        generate_export: bool = True,
        notify: bool = True,
    ) -> PipelineResult:
        started = time.perf_counter()
        now = utcnow()
        metrics = PipelineMetrics()
        run = await self.runs.create(trigger=trigger, source_filter=source_name)
        await self.runs.start(run, now=now)
        await self.session.commit()
        bind_run_context(run_id=str(run.id), task="pipeline")
        logger.info("pipeline_started", source_filter=source_name, trigger=trigger)
        step_status: dict[str, str] = {name: StepStatus.PENDING for name in PIPELINE_STEPS}

        try:
            connectors = enabled_sources(only=source_name, mutate_demo=mutate_demo)
            source_rows: dict[str, Source] = {}
            for name, config, _connector in connectors:
                source_rows[name] = await self.sources.upsert(
                    name=name,
                    source_type=config.type,
                    enabled=config.enabled,
                    description=config.description,
                    config=config.model_dump(mode="json"),
                )
            await self.session.commit()

            collection_started = utcnow()
            fetched, source_errors = await self._collect(connectors)
            metrics.sources_attempted = len(connectors)
            metrics.sources_successful = metrics.sources_attempted - len(source_errors)
            metrics.sources_failed = len(source_errors)
            metrics.records_discovered = sum(len(items) for items in fetched.values())
            collection_status = (
                StepStatus.SUCCESS
                if not source_errors
                else (StepStatus.PARTIAL_SUCCESS if fetched else StepStatus.FAILED)
            )
            await self.runs.add_step(
                run,
                name="collection",
                status=collection_status,
                started_at=collection_started,
                finished_at=utcnow(),
                details={"failed_sources": list(source_errors)},
            )
            step_status["collection"] = collection_status
            step_status["extraction"] = StepStatus.SUCCESS
            await self.runs.add_step(
                run,
                name="extraction",
                status=StepStatus.SUCCESS,
                started_at=collection_started,
                finished_at=utcnow(),
                details={"records": metrics.records_discovered},
            )

            existing_pool = list(await self.opportunities.recent_for_matching())
            processed_new: list[Opportunity] = []
            major_changes: list[Opportunity] = []

            for name, raw_records in fetched.items():
                source = source_rows[name]
                accepted = 0
                rejected = 0
                for raw in raw_records:
                    try:
                        outcome = await self._process_record(
                            raw,
                            source=source,
                            run_id=run.id,
                            existing_pool=existing_pool,
                            metrics=metrics,
                        )
                    except Exception as exc:  # noqa: BLE001 — isolate per record
                        rejected += 1
                        metrics.invalid_records += 1
                        await self.runs.add_error(
                            run_id=run.id,
                            source_id=source.id,
                            external_id=raw.external_id,
                            error_type=type(exc).__name__,
                            error_message=str(exc),
                            raw_payload=raw.model_dump(mode="json"),
                        )
                        logger.warning(
                            "record_failed",
                            source=name,
                            error_type=type(exc).__name__,
                            record_id=raw.external_id,
                        )
                        continue
                    if outcome == "invalid":
                        rejected += 1
                    else:
                        accepted += 1
                    if isinstance(outcome, Opportunity) and outcome not in existing_pool:
                        existing_pool.append(outcome)
                        processed_new.append(outcome)
                    if isinstance(outcome, tuple) and outcome[0] == "updated" and outcome[2]:
                        major_changes.append(outcome[1])

                await self.sources.record_success(
                    source,
                    now=utcnow(),
                    duration_ms=0,
                    http_status=200,
                    discovered=len(raw_records),
                    accepted=accepted,
                    rejected=rejected,
                )

            for name, error in source_errors.items():
                source = source_rows[name]
                status_code = getattr(error, "status_code", None)
                await self.sources.record_failure(source, now=utcnow(), http_status=status_code)
                await self.runs.add_error(
                    run_id=run.id,
                    source_id=source.id,
                    external_id=None,
                    error_type=type(error).__name__,
                    error_message=str(error),
                    raw_payload={"source": name},
                )

            for step in ("validation", "normalisation", "deduplication", "scoring", "persistence"):
                await self.runs.add_step(
                    run,
                    name=step,
                    status=StepStatus.SUCCESS,
                    started_at=collection_started,
                    finished_at=utcnow(),
                    details={},
                )
                step_status[step] = StepStatus.SUCCESS

            export_path = None
            if generate_export:
                reporting_started = utcnow()
                try:
                    all_opps = list(await self.opportunities.list_all())
                    export_path = await asyncio.to_thread(
                        self.reporter.export_all,
                        all_opps,
                        metrics.as_dict(),
                        run.id,
                    )
                    await self.exports.create(
                        format="xlsx",
                        path=str(export_path),
                        record_count=len(all_opps),
                        run_id=run.id,
                    )
                    metrics.export_path = str(export_path)
                    await self.runs.add_step(
                        run,
                        name="reporting",
                        status=StepStatus.SUCCESS,
                        started_at=reporting_started,
                        finished_at=utcnow(),
                        details={"path": str(export_path)},
                    )
                    step_status["reporting"] = StepStatus.SUCCESS
                except Exception as exc:  # noqa: BLE001
                    await self.runs.add_step(
                        run,
                        name="reporting",
                        status=StepStatus.FAILED,
                        started_at=reporting_started,
                        finished_at=utcnow(),
                        error_message=str(exc),
                    )
                    step_status["reporting"] = StepStatus.FAILED
                    logger.warning("reporting_failed", error=str(exc))
            else:
                step_status["reporting"] = StepStatus.SKIPPED

            notify_status = StepStatus.SKIPPED
            if notify:
                notify_started = utcnow()
                high_priority = [
                    item
                    for item in processed_new
                    if item.score >= self.scorer.config.minimum_score_for_alert
                ]
                metrics.high_priority_opportunities = len(
                    [
                        item
                        for item in existing_pool
                        if item.score >= self.scorer.config.minimum_score_for_alert
                    ]
                )
                closing = [
                    item
                    for item in existing_pool
                    if item.days_remaining is not None
                    and 0 <= item.days_remaining <= self.scorer.config.closing_soon_days
                ]
                failing = [row for row in source_rows.values() if row.consecutive_failures >= 3]
                notify_status = await self.notifier.dispatch_run(
                    run_id=run.id,
                    new_high=high_priority,
                    closing=closing,
                    major_changes=major_changes,
                    failing_sources=failing,
                )
                await self.runs.add_step(
                    run,
                    name="notification",
                    status=notify_status,
                    started_at=notify_started,
                    finished_at=utcnow(),
                )
            step_status["notification"] = notify_status

            metrics.duration_seconds = time.perf_counter() - started
            status = RunStatus.SUCCESS if metrics.sources_failed == 0 else RunStatus.PARTIAL_SUCCESS
            if metrics.sources_successful == 0 and metrics.sources_attempted > 0:
                status = RunStatus.FAILED
            await self.runs.finish(run, status=status, now=utcnow(), metrics=metrics.as_dict())
            await self.session.commit()
            logger.info("pipeline_finished", status=status, **metrics.as_dict())
            return PipelineResult(run_id=run.id, status=status, metrics=metrics, steps=step_status)
        except Exception as exc:
            await self.session.rollback()
            metrics.duration_seconds = time.perf_counter() - started
            logger.exception("pipeline_failed", error_type=type(exc).__name__)
            try:
                await self.runs.finish(
                    run,
                    status=RunStatus.FAILED,
                    now=utcnow(),
                    metrics=metrics.as_dict(),
                    error_message=str(exc),
                )
                await self.session.commit()
            except Exception:
                await self.session.rollback()
            raise
        finally:
            clear_run_context()

    async def _collect(
        self,
        connectors: list[tuple[str, Any, Any]],
    ) -> tuple[dict[str, list[RawOpportunityIn]], dict[str, Exception]]:
        async def _one(name: str, connector: Any) -> tuple[str, list[RawOpportunityIn] | Exception]:
            started = time.perf_counter()
            try:
                records = await connector.fetch()
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.info(
                    "source_fetched",
                    source=name,
                    records=len(records),
                    duration_ms=duration_ms,
                    status="success",
                )
                return name, records
            except Exception as exc:  # noqa: BLE001 — source isolation
                duration_ms = int((time.perf_counter() - started) * 1000)
                logger.warning(
                    "source_failed",
                    source=name,
                    duration_ms=duration_ms,
                    status="failed",
                    error_type=type(exc).__name__,
                )
                return name, exc

        results = await asyncio.gather(
            *[_one(name, connector) for name, _, connector in connectors]
        )
        fetched: dict[str, list[RawOpportunityIn]] = {}
        errors: dict[str, Exception] = {}
        for name, payload in results:
            if isinstance(payload, Exception):
                errors[name] = payload
            else:
                fetched[name] = payload
        return fetched, errors

    async def _process_record(
        self,
        raw: RawOpportunityIn,
        *,
        source: Source,
        run_id: uuid.UUID,
        existing_pool: list[Opportunity],
        metrics: PipelineMetrics,
    ) -> str | Opportunity | tuple[str, Opportunity, bool]:
        if not raw.content_hash:
            raw.content_hash = content_hash_from_raw(
                title=raw.raw_title,
                description=raw.raw_description,
                organisation=raw.raw_organisation,
                location=raw.raw_location,
                value=raw.raw_value,
                deadline=raw.raw_deadline,
                url=raw.source_url,
                extra=raw.raw_metadata,
            )
        try:
            self.validator.validate_raw(raw)
            normalised = self.normaliser.normalise(raw)
            self.validator.validate_normalised(normalised)
        except RecordValidationError as exc:
            metrics.invalid_records += 1
            await self.runs.add_error(
                run_id=run_id,
                source_id=source.id,
                external_id=raw.external_id,
                error_type="RecordValidationError",
                error_message=exc.message,
                raw_payload=raw.model_dump(mode="json"),
            )
            return "invalid"

        raw_row = await self.opportunities.add_raw(
            source_id=source.id,
            run_id=run_id,
            external_id=raw.external_id,
            source_url=raw.source_url,
            retrieved_at=raw.retrieved_at,
            raw_title=raw.raw_title,
            raw_description=raw.raw_description,
            raw_organisation=raw.raw_organisation,
            raw_location=raw.raw_location,
            raw_value=raw.raw_value,
            raw_deadline=raw.raw_deadline,
            raw_metadata=raw.raw_metadata,
            content_hash=raw.content_hash or normalised.content_hash,
            http_status=raw.http_status,
            http_headers=raw.http_headers,
        )

        identity = await self.opportunities.find_identity(
            source_id=source.id,
            external_id=normalised.external_id,
            canonical_url=normalised.canonical_url,
            fingerprint=normalised.fingerprint,
            content_hash=normalised.content_hash,
        )
        scored = self.scorer.score(normalised)

        if identity is not None:
            return await self._handle_existing(
                identity, scored, normalised, run_id=run_id, metrics=metrics
            )

        for candidate in existing_pool:
            decision = self.deduper.compare(
                normalised, candidate, same_source=candidate.source_id == source.id
            )
            if decision.status == DuplicateStatus.CONFIRMED and decision.matched:
                metrics.duplicates += 1
                await self.opportunities.add_duplicate(
                    opportunity_id=decision.matched.id,
                    candidate_id=decision.matched.id,
                    confidence=decision.confidence,
                    signals=decision.signals,
                    status=decision.status,
                    reason=decision.reason,
                )
                await self.opportunities.touch(decision.matched)
                return "duplicate"
            if decision.status == DuplicateStatus.AMBIGUOUS and decision.matched:
                metrics.ambiguous_duplicates += 1
                await self.opportunities.add_duplicate(
                    opportunity_id=decision.matched.id,
                    candidate_id=decision.matched.id,
                    confidence=decision.confidence,
                    signals=decision.signals,
                    status=decision.status,
                    reason=decision.reason,
                )
                # Keep the raw row for provenance, but do not insert a second
                # opportunity. Borderline matches must not explode on re-runs.
                return "ambiguous"

        inserted = await self.opportunities.insert_scored(
            scored, source_id=source.id, raw_id=raw_row.id
        )
        metrics.new_records += 1
        return inserted

    async def _handle_existing(
        self,
        existing: Opportunity,
        scored: ScoredOpportunity,
        normalised: NormalisedOpportunity,
        *,
        run_id: uuid.UUID,
        metrics: PipelineMetrics,
    ) -> str | tuple[str, Opportunity, bool]:
        if existing.content_hash == scored.content_hash:
            metrics.duplicates += 1
            await self.opportunities.touch(existing)
            return "duplicate"
        changes = self.changes.diff(existing, normalised)
        major = self.changes.is_major(changes)
        for change in changes:
            await self.opportunities.add_history(
                opportunity_id=existing.id,
                run_id=run_id,
                field_name=change["field_name"] or "",
                previous_value=change["previous_value"],
                new_value=change["new_value"],
                detected_at=utcnow(),
            )
        await self.opportunities.apply_update(existing, scored)
        metrics.updated_records += 1
        return ("updated", existing, major)
