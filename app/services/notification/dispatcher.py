"""Dispatch pipeline events to configured providers and persist an audit trail."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import NotificationEvent, NotificationStatus, StepStatus
from app.db.models.opportunity import Opportunity
from app.db.models.source import Source
from app.repositories.notification import NotificationRepository
from app.schemas.notification import Notification
from app.services.normalisation.dates import utcnow
from app.services.notification.base import NotificationProvider
from app.services.notification.console import ConsoleNotificationProvider
from app.services.notification.email import EmailNotificationProvider
from app.services.notification.webhook import WebhookNotificationProvider


class NotificationDispatcher:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = NotificationRepository(session)
        settings = get_settings()
        self.providers: list[NotificationProvider] = [ConsoleNotificationProvider()]
        if settings.email_enabled:
            self.providers.append(EmailNotificationProvider())
        if settings.webhook_enabled:
            self.providers.append(WebhookNotificationProvider())

    async def dispatch_run(
        self,
        *,
        run_id: UUID,
        new_high: list[Opportunity],
        closing: list[Opportunity],
        major_changes: list[Opportunity],
        failing_sources: list[Source],
    ) -> StepStatus:
        events: list[Notification] = []
        now = utcnow()
        for item in new_high[:10]:
            events.append(
                Notification(
                    event=NotificationEvent.NEW_HIGH_PRIORITY,
                    timestamp=now,
                    title=f"High-priority opportunity: {item.title}",
                    body=f"{item.organisation or 'Unknown'} scored {item.score} ({item.score_rating}).",
                    data={"score": item.score, "url": item.source_url},
                    opportunity_id=item.id,
                    run_id=run_id,
                )
            )
        for item in closing[:10]:
            events.append(
                Notification(
                    event=NotificationEvent.CLOSING_SOON,
                    timestamp=now,
                    title=f"Closing soon: {item.title}",
                    body=f"Deadline status {item.deadline_status}; {item.days_remaining} day(s) remaining.",
                    data={"deadline": item.deadline_at.isoformat() if item.deadline_at else None},
                    opportunity_id=item.id,
                    run_id=run_id,
                )
            )
        for item in major_changes[:10]:
            events.append(
                Notification(
                    event=NotificationEvent.MAJOR_CHANGE,
                    timestamp=now,
                    title=f"Major change: {item.title}",
                    body="An existing opportunity changed a high-impact field (deadline, value, status or description).",
                    opportunity_id=item.id,
                    run_id=run_id,
                )
            )
        for source in failing_sources:
            events.append(
                Notification(
                    event=NotificationEvent.SOURCE_FAILING,
                    timestamp=now,
                    title=f"Source unhealthy: {source.name}",
                    body=f"{source.consecutive_failures} consecutive failures.",
                    data={"source": source.name, "health": source.health_status},
                    run_id=run_id,
                )
            )

        if not events:
            return StepStatus.SKIPPED

        failures = 0
        successes = 0
        for event in events:
            for provider in self.providers:
                result = await provider.send(event)
                status = NotificationStatus.SENT if result.success else NotificationStatus.FAILED
                if result.success:
                    successes += 1
                else:
                    failures += 1
                await self.repo.create(
                    event_type=event.event,
                    provider=provider.name,
                    status=status,
                    payload=event.model_dump(mode="json"),
                    opportunity_id=event.opportunity_id,
                    run_id=run_id,
                    sent_at=now if result.success else None,
                    error_message=None if result.success else result.message,
                )
        if failures and successes:
            return StepStatus.PARTIAL_SUCCESS
        if failures:
            return StepStatus.FAILED
        return StepStatus.SUCCESS
