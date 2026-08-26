"""Deduplication signal tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.core.enums import DuplicateStatus
from app.schemas.opportunity import NormalisedOpportunity
from app.services.deduplication.engine import DeduplicationEngine


def _incoming(**overrides: object) -> NormalisedOpportunity:
    payload = {
        "source_name": "demo",
        "external_id": "DEMO-0001",
        "title": "Python Data Extraction Automation",
        "organisation": "Northbridge Digital Services",
        "description": "Collect and normalise supplier data.",
        "source_url": "https://opportunities.example.invalid/northbridge/1",
        "canonical_url": "https://opportunities.example.invalid/northbridge/1",
        "content_hash": "c" * 64,
        "fingerprint": "d" * 64,
        "deadline_at": datetime(2026, 9, 1, tzinfo=UTC),
        "normalised_title": "python data extraction automation",
        "normalised_organisation": "northbridge digital",
    }
    payload.update(overrides)
    return NormalisedOpportunity.model_validate(payload)


def _existing(**overrides: object) -> SimpleNamespace:
    data = {
        "id": uuid.uuid4(),
        "source_id": uuid.uuid4(),
        "external_id": "DEMO-0001",
        "title": "Python Data Extraction Automation",
        "organisation": "Northbridge Digital Services",
        "canonical_url": "https://opportunities.example.invalid/northbridge/1",
        "content_hash": "c" * 64,
        "fingerprint": "d" * 64,
        "deadline_at": datetime(2026, 9, 1, tzinfo=UTC),
        "normalised_title": "python data extraction automation",
        "normalised_organisation": "northbridge digital",
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_duplicate_source_id() -> None:
    decision = DeduplicationEngine().compare(_incoming(), _existing(), same_source=True)
    assert decision.duplicate is True
    assert decision.status == DuplicateStatus.CONFIRMED
    assert decision.signals.get("exact_source_id") is True


def test_duplicate_url() -> None:
    incoming = _incoming(external_id="OTHER")
    existing = _existing(external_id="DIFFERENT")
    decision = DeduplicationEngine().compare(incoming, existing, same_source=False)
    assert decision.duplicate is True
    assert decision.signals.get("canonical_url") is True


def test_similar_title_confirmed() -> None:
    incoming = _incoming(
        external_id="NEAR",
        canonical_url="https://opportunities.example.invalid/other",
        source_url="https://opportunities.example.invalid/other",
        content_hash="e" * 64,
        title="Python Data Extraction Automation Programme",
        normalised_title="python data extraction automation programme",
    )
    existing = _existing(
        external_id="ORIG",
        canonical_url="https://elsewhere.example.invalid/x",
        content_hash="f" * 64,
    )
    decision = DeduplicationEngine().compare(incoming, existing, same_source=False)
    assert decision.status in {DuplicateStatus.CONFIRMED, DuplicateStatus.AMBIGUOUS}
    assert decision.signals["title_similarity"] > 0.7


def test_different_organisation_not_auto_merged() -> None:
    incoming = _incoming(
        external_id="DIFF",
        organisation="Kingswell Water Partnership",
        normalised_organisation="kingswell water",
        canonical_url="https://opportunities.example.invalid/kingswell/1",
        source_url="https://opportunities.example.invalid/kingswell/1",
        content_hash="1" * 64,
    )
    existing = _existing(
        external_id="ORIG",
        canonical_url="https://elsewhere.example.invalid/x",
        content_hash="2" * 64,
    )
    decision = DeduplicationEngine().compare(incoming, existing, same_source=False)
    assert (
        decision.status != DuplicateStatus.CONFIRMED
        or decision.signals.get("organisation_match") is False
    )
