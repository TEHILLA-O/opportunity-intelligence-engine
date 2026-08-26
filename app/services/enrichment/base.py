"""Optional enrichment adapter. The pipeline never depends on this being enabled."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.opportunity import NormalisedOpportunity


class EnrichmentProvider(ABC):
    name: str

    @abstractmethod
    async def enrich(self, record: NormalisedOpportunity) -> NormalisedOpportunity:
        """Return the record, optionally with summary/keyword/category suggestions."""
