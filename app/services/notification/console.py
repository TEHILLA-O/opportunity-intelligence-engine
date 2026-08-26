"""Always-on console notification provider for local demos."""

from __future__ import annotations

from rich.console import Console

from app.schemas.notification import Notification, NotificationResult
from app.services.notification.base import NotificationProvider

_console = Console()


class ConsoleNotificationProvider(NotificationProvider):
    name = "console"

    async def send(self, notification: Notification) -> NotificationResult:
        _console.print(
            f"[bold cyan]ALERT[/] [{notification.event}] {notification.title}\n"
            f"  {notification.body}"
        )
        return NotificationResult(provider=self.name, success=True)
