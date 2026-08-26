"""Generic outbound webhook. Optional; disabled without WEBHOOK_URL."""

from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.schemas.notification import Notification, NotificationResult
from app.services.notification.base import NotificationProvider


class WebhookNotificationProvider(NotificationProvider):
    name = "webhook"

    async def send(self, notification: Notification) -> NotificationResult:
        settings = get_settings()
        if not settings.webhook_enabled:
            return NotificationResult(
                provider=self.name, success=False, message="WEBHOOK_URL not configured"
            )
        payload = {
            "event": notification.event,
            "timestamp": notification.timestamp.isoformat(),
            "data": {
                "title": notification.title,
                "body": notification.body,
                **notification.data,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(settings.webhook_url, json=payload)
            if response.status_code >= 400:
                return NotificationResult(
                    provider=self.name,
                    success=False,
                    message=f"HTTP {response.status_code}",
                )
            return NotificationResult(provider=self.name, success=True)
        except Exception as exc:  # noqa: BLE001
            return NotificationResult(provider=self.name, success=False, message=str(exc))
