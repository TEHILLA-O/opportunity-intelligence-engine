"""Optional enrichment adapters. Default is deterministic / no-AI."""

from app.services.enrichment.base import EnrichmentProvider
from app.services.enrichment.noop import get_enrichment_provider

__all__ = ["EnrichmentProvider", "get_enrichment_provider"]
