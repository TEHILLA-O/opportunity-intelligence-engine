"""Notification provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.notification import Notification, NotificationResult


class NotificationProvider(ABC):
    name: str

    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult:
        """Deliver a notification. Implementations must not raise for expected failures."""
