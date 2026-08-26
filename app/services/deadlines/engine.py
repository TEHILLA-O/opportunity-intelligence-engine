"""Deadline urgency classification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.constants import (
    DEADLINE_CRITICAL_DAYS,
    DEADLINE_NORMAL_DAYS,
    DEADLINE_UPCOMING_DAYS,
    DEADLINE_URGENT_DAYS,
)
from app.core.enums import DeadlineStatus
from app.services.normalisation.dates import ensure_utc, utcnow


@dataclass(frozen=True)
class DeadlineEvaluation:
    status: DeadlineStatus
    days_remaining: int | None
    expired: bool


class DeadlineEngine:
    def evaluate(
        self, deadline_at: datetime | None, *, now: datetime | None = None
    ) -> DeadlineEvaluation:
        if deadline_at is None:
            return DeadlineEvaluation(DeadlineStatus.UNKNOWN, None, False)
        current = ensure_utc(now) or utcnow()
        aware_deadline = ensure_utc(deadline_at)
        if aware_deadline is None:
            return DeadlineEvaluation(DeadlineStatus.UNKNOWN, None, False)
        delta = aware_deadline - current
        days = int(delta.total_seconds() // 86400)
        if delta.total_seconds() < 0:
            return DeadlineEvaluation(DeadlineStatus.EXPIRED, days, True)
        if days <= DEADLINE_CRITICAL_DAYS:
            return DeadlineEvaluation(DeadlineStatus.CRITICAL, max(days, 0), False)
        if days <= DEADLINE_URGENT_DAYS:
            return DeadlineEvaluation(DeadlineStatus.URGENT, days, False)
        if days <= DEADLINE_UPCOMING_DAYS:
            return DeadlineEvaluation(DeadlineStatus.UPCOMING, days, False)
        if days <= DEADLINE_NORMAL_DAYS:
            return DeadlineEvaluation(DeadlineStatus.NORMAL, days, False)
        return DeadlineEvaluation(DeadlineStatus.NORMAL, days, False)
