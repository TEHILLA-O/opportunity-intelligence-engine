"""Abstract source connector and health result."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.raw import RawOpportunityIn, SourceHealth


class OpportunitySource(ABC):
    """Every connector exposes the same fetch/healthcheck contract."""

    name: str

    @abstractmethod
    async def fetch(self) -> list[RawOpportunityIn]:
        """Collect raw opportunities from the upstream source."""

    @abstractmethod
    async def healthcheck(self) -> SourceHealth:
        """Cheap availability probe that must not mutate state."""
