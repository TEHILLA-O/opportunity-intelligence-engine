"""Scoring and exclusion-keyword tests."""

from __future__ import annotations

from app.schemas.opportunity import NormalisedOpportunity
from app.services.scoring.engine import ScoringEngine


def _record(**overrides: object) -> NormalisedOpportunity:
    payload = {
        "source_name": "demo",
        "title": "Python Data Extraction Automation",
        "organisation": "Northbridge Digital Services",
        "description": "Build a Python automation and ETL platform with FastAPI and PostgreSQL.",
        "category": "automation",
        "location": "Remote, United Kingdom",
        "content_hash": "a" * 64,
        "fingerprint": "b" * 64,
        "source_url": "https://opportunities.example.invalid/python-etl",
        "skills": ["Python", "ETL"],
        "contract_type": "fixed_price",
        "procurement_type": "tender",
        "remote_status": "remote",
    }
    payload.update(overrides)
    return NormalisedOpportunity.model_validate(payload)


def test_score_is_explainable() -> None:
    scored = ScoringEngine().score(_record())
    assert 0 <= scored.score <= 100
    assert scored.score_reasons
    assert any("python" in reason.lower() for reason in scored.score_reasons)


def test_exclusion_keyword_reduces_score() -> None:
    high = ScoringEngine().score(_record())
    low = ScoringEngine().score(
        _record(
            title="WordPress Brochure Site Redesign",
            description="Graphic design and WordPress theme work.",
            category="graphic-design",
            skills=["Graphic design"],
            contract_type="unknown",
        )
    )
    assert high.score > low.score
    assert any(
        "excluded" in reason.lower() or "wordpress" in reason.lower()
        for reason in low.score_reasons
    )
