"""Optional SMTP notification provider. Disabled unless SMTP_HOST is set."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.schemas.notification import Notification, NotificationResult
from app.services.notification.base import NotificationProvider


class EmailNotificationProvider(NotificationProvider):
    name = "email"

    async def send(self, notification: Notification) -> NotificationResult:
        settings = get_settings()
        if not settings.email_enabled:
            return NotificationResult(
                provider=self.name, success=False, message="SMTP not configured"
            )
        message = EmailMessage()
        message["Subject"] = f"[Opportunity Engine] {notification.title}"
        message["From"] = settings.smtp_from
        message["To"] = settings.smtp_from
        message.set_content(notification.body)
        try:
            await asyncio.to_thread(self._deliver, message)
            return NotificationResult(provider=self.name, success=True)
        except Exception as exc:  # noqa: BLE001
            return NotificationResult(provider=self.name, success=False, message=str(exc))

    def _deliver(self, message: EmailMessage) -> None:
        settings = get_settings()
        password = settings.smtp_password.get_secret_value()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username:
                smtp.login(settings.smtp_username, password)
            smtp.send_message(message)
