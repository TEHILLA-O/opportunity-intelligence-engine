"""Deterministic no-op enrichment used when AI is disabled (the default)."""

from __future__ import annotations

from app.schemas.opportunity import NormalisedOpportunity
from app.services.enrichment.base import EnrichmentProvider
from app.services.normalisation.text import extract_keywords, summarise


class NoOpEnrichmentProvider(EnrichmentProvider):
    name = "none"

    async def enrich(self, record: NormalisedOpportunity) -> NormalisedOpportunity:
        return record


class EchoEnrichmentProvider(EnrichmentProvider):
    """Local, deterministic stand-in used to prove the adapter without a vendor SDK."""

    name = "echo"

    async def enrich(self, record: NormalisedOpportunity) -> NormalisedOpportunity:
        if not record.summary:
            record.summary = summarise(record.description or record.title)
        if not record.keywords:
            record.keywords = extract_keywords(
                " ".join(filter(None, [record.title, record.description]))
            )
        return record


def get_enrichment_provider(name: str = "none") -> EnrichmentProvider:
    if name == "echo":
        return EchoEnrichmentProvider()
    return NoOpEnrichmentProvider()
