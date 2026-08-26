"""Opportunity, raw record, history and duplicate persistence."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import DeadlineStatus, ScoreRating
from app.db.models.opportunity import (
    DuplicateCandidate,
    Opportunity,
    OpportunityHistory,
    RawOpportunity,
)
from app.db.models.source import Source
from app.schemas.api import OpportunityFilters
from app.schemas.opportunity import ScoredOpportunity
from app.services.normalisation.dates import utcnow


class OpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_raw(
        self,
        *,
        source_id: uuid.UUID,
        run_id: uuid.UUID | None,
        external_id: str | None,
        source_url: str | None,
        retrieved_at: datetime,
        raw_title: str | None,
        raw_description: str | None,
        raw_organisation: str | None,
        raw_location: str | None,
        raw_value: str | None,
        raw_deadline: str | None,
        raw_metadata: dict[str, Any],
        content_hash: str,
        http_status: int | None,
        http_headers: dict[str, Any] | None,
    ) -> RawOpportunity:
        record = RawOpportunity(
            source_id=source_id,
            run_id=run_id,
            external_id=external_id,
            source_url=source_url,
            retrieved_at=retrieved_at,
            raw_title=raw_title,
            raw_description=raw_description,
            raw_organisation=raw_organisation,
            raw_location=raw_location,
            raw_value=raw_value,
            raw_deadline=raw_deadline,
            raw_metadata=raw_metadata,
            content_hash=content_hash,
            http_status=http_status,
            http_headers=http_headers,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def find_identity(
        self,
        *,
        source_id: uuid.UUID,
        external_id: str | None,
        canonical_url: str | None,
        fingerprint: str | None,
        content_hash: str | None,
    ) -> Opportunity | None:
        if external_id:
            result = await self.session.execute(
                select(Opportunity).where(
                    Opportunity.source_id == source_id, Opportunity.external_id == external_id
                )
            )
            found = result.scalar_one_or_none()
            if found:
                return found
        if canonical_url:
            result = await self.session.execute(
                select(Opportunity).where(Opportunity.canonical_url == canonical_url)
            )
            found = result.scalar_one_or_none()
            if found:
                return found
        if content_hash:
            result = await self.session.execute(
                select(Opportunity).where(Opportunity.content_hash == content_hash)
            )
            found = result.scalar_one_or_none()
            if found:
                return found
        if fingerprint:
            result = await self.session.execute(
                select(Opportunity).where(Opportunity.fingerprint == fingerprint)
            )
            return result.scalar_one_or_none()
        return None

    async def recent_for_matching(self, *, limit: int = 400) -> Sequence[Opportunity]:
        result = await self.session.execute(
            select(Opportunity).order_by(Opportunity.last_seen_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def insert_scored(
        self,
        scored: ScoredOpportunity,
        *,
        source_id: uuid.UUID,
        raw_id: uuid.UUID | None,
        now: datetime | None = None,
    ) -> Opportunity:
        stamp = now or utcnow()
        record = Opportunity(
            source_id=source_id,
            raw_opportunity_id=raw_id,
            external_id=scored.external_id,
            title=scored.title,
            organisation=scored.organisation,
            description=scored.description,
            summary=scored.summary,
            category=scored.category,
            location=scored.location,
            country=scored.country,
            remote_status=scored.remote_status,
            procurement_type=scored.procurement_type,
            contract_type=scored.contract_type,
            currency=scored.currency,
            minimum_value=scored.minimum_value,
            maximum_value=scored.maximum_value,
            estimated_value=scored.estimated_value,
            published_at=scored.published_at,
            deadline_at=scored.deadline_at,
            source_url=scored.source_url,
            canonical_url=scored.canonical_url,
            contact_name=scored.contact_name,
            contact_email=str(scored.contact_email) if scored.contact_email else None,
            requirements=scored.requirements,
            skills=scored.skills,
            keywords=scored.keywords,
            status=scored.status,
            score=scored.score,
            score_rating=scored.score_rating,
            score_reasons=scored.score_reasons,
            deadline_status=scored.deadline_status,
            days_remaining=scored.days_remaining,
            first_seen_at=stamp,
            last_seen_at=stamp,
            content_hash=scored.content_hash,
            fingerprint=scored.fingerprint,
            normalised_title=scored.normalised_title,
            normalised_organisation=scored.normalised_organisation,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def touch(self, record: Opportunity, *, now: datetime | None = None) -> None:
        record.last_seen_at = now or utcnow()
        await self.session.flush()

    async def apply_update(
        self,
        record: Opportunity,
        scored: ScoredOpportunity,
        *,
        now: datetime | None = None,
    ) -> None:
        stamp = now or utcnow()
        record.title = scored.title
        record.organisation = scored.organisation
        record.description = scored.description
        record.summary = scored.summary
        record.category = scored.category
        record.location = scored.location
        record.country = scored.country
        record.remote_status = scored.remote_status
        record.procurement_type = scored.procurement_type
        record.contract_type = scored.contract_type
        record.currency = scored.currency
        record.minimum_value = scored.minimum_value
        record.maximum_value = scored.maximum_value
        record.estimated_value = scored.estimated_value
        record.published_at = scored.published_at
        record.deadline_at = scored.deadline_at
        record.source_url = scored.source_url
        record.canonical_url = scored.canonical_url
        record.contact_name = scored.contact_name
        record.contact_email = str(scored.contact_email) if scored.contact_email else None
        record.requirements = scored.requirements
        record.skills = scored.skills
        record.keywords = scored.keywords
        record.status = scored.status
        record.score = scored.score
        record.score_rating = scored.score_rating
        record.score_reasons = scored.score_reasons
        record.deadline_status = scored.deadline_status
        record.days_remaining = scored.days_remaining
        record.content_hash = scored.content_hash
        record.fingerprint = scored.fingerprint
        record.normalised_title = scored.normalised_title
        record.normalised_organisation = scored.normalised_organisation
        record.last_seen_at = stamp
        await self.session.flush()

    async def add_history(
        self,
        *,
        opportunity_id: uuid.UUID,
        run_id: uuid.UUID | None,
        field_name: str,
        previous_value: str | None,
        new_value: str | None,
        detected_at: datetime,
    ) -> OpportunityHistory:
        row = OpportunityHistory(
            opportunity_id=opportunity_id,
            run_id=run_id,
            field_name=field_name,
            previous_value=previous_value,
            new_value=new_value,
            detected_at=detected_at,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_duplicate(
        self,
        *,
        opportunity_id: uuid.UUID,
        candidate_id: uuid.UUID,
        confidence: Any,
        signals: dict[str, Any],
        status: str,
        reason: str | None,
    ) -> DuplicateCandidate:
        existing = await self.session.execute(
            select(DuplicateCandidate).where(
                DuplicateCandidate.opportunity_id == opportunity_id,
                DuplicateCandidate.candidate_id == candidate_id,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.confidence = confidence
            row.signals = signals
            row.status = status
            row.reason = reason
            await self.session.flush()
            return row
        row = DuplicateCandidate(
            opportunity_id=opportunity_id,
            candidate_id=candidate_id,
            confidence=confidence,
            signals=signals,
            status=status,
            reason=reason,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    def _filtered_query(self, filters: OpportunityFilters | None) -> Select[tuple[Opportunity]]:
        stmt = select(Opportunity)
        if not filters:
            return stmt
        if filters.min_score is not None:
            stmt = stmt.where(Opportunity.score >= filters.min_score)
        if filters.max_score is not None:
            stmt = stmt.where(Opportunity.score <= filters.max_score)
        if filters.organisation:
            stmt = stmt.where(Opportunity.organisation.ilike(f"%{filters.organisation}%"))
        if filters.category:
            stmt = stmt.where(Opportunity.category.ilike(f"%{filters.category}%"))
        if filters.status:
            stmt = stmt.where(Opportunity.status == filters.status)
        if filters.rating:
            stmt = stmt.where(Opportunity.score_rating == filters.rating)
        if filters.deadline_status:
            stmt = stmt.where(Opportunity.deadline_status == filters.deadline_status)
        if filters.deadline_from:
            stmt = stmt.where(Opportunity.deadline_at >= filters.deadline_from)
        if filters.deadline_to:
            stmt = stmt.where(Opportunity.deadline_at <= filters.deadline_to)
        if filters.value_min is not None:
            stmt = stmt.where(Opportunity.estimated_value >= filters.value_min)
        if filters.value_max is not None:
            stmt = stmt.where(Opportunity.estimated_value <= filters.value_max)
        if filters.first_seen_from:
            stmt = stmt.where(Opportunity.first_seen_at >= filters.first_seen_from)
        if filters.first_seen_to:
            stmt = stmt.where(Opportunity.first_seen_at <= filters.first_seen_to)
        if filters.keyword:
            pattern = f"%{filters.keyword}%"
            stmt = stmt.where(
                or_(
                    Opportunity.title.ilike(pattern),
                    Opportunity.description.ilike(pattern),
                    Opportunity.summary.ilike(pattern),
                )
            )
        return stmt

    async def list_filtered(
        self,
        filters: OpportunityFilters | None,
        *,
        page: int,
        page_size: int,
        sort: str,
        order: str,
        source_name: str | None = None,
    ) -> tuple[list[Opportunity], int]:
        stmt = self._filtered_query(filters)
        if source_name:
            stmt = stmt.join(Source, Opportunity.source_id == Source.id).where(
                Source.name == source_name
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int(await self.session.scalar(count_stmt) or 0)
        sort_column = getattr(Opportunity, sort, Opportunity.score)
        stmt = stmt.order_by(sort_column.asc() if order == "asc" else sort_column.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get(self, opportunity_id: uuid.UUID) -> Opportunity | None:
        return await self.session.get(Opportunity, opportunity_id)

    async def list_all(self) -> Sequence[Opportunity]:
        result = await self.session.execute(select(Opportunity).order_by(Opportunity.score.desc()))
        return result.scalars().all()

    async def count(self) -> int:
        return int(await self.session.scalar(select(func.count()).select_from(Opportunity)) or 0)

    async def count_rating(self, rating: ScoreRating) -> int:
        return int(
            await self.session.scalar(
                select(func.count()).where(Opportunity.score_rating == rating)
            )
            or 0
        )

    async def count_deadline(self, status: DeadlineStatus) -> int:
        return int(
            await self.session.scalar(
                select(func.count()).where(Opportunity.deadline_status == status)
            )
            or 0
        )

    async def high_priority(self, *, min_score: int = 65, limit: int = 20) -> Sequence[Opportunity]:
        result = await self.session.execute(
            select(Opportunity)
            .where(Opportunity.score >= min_score)
            .order_by(Opportunity.score.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def closing_soon(self, *, limit: int = 20) -> Sequence[Opportunity]:
        result = await self.session.execute(
            select(Opportunity)
            .where(
                Opportunity.deadline_status.in_(
                    [DeadlineStatus.CRITICAL, DeadlineStatus.URGENT, DeadlineStatus.UPCOMING]
                )
            )
            .order_by(Opportunity.deadline_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    async def newest(self, *, limit: int = 20) -> Sequence[Opportunity]:
        result = await self.session.execute(
            select(Opportunity).order_by(Opportunity.first_seen_at.desc()).limit(limit)
        )
        return result.scalars().all()
