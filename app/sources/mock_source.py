"""Bundled mock source — no network required."""

from __future__ import annotations

from app.schemas.raw import RawOpportunityIn, SourceHealth
from app.services.deduplication.fingerprint import content_hash_from_raw
from app.services.normalisation.dates import utcnow
from app.sources.base import OpportunitySource
from app.sources.demo_dataset import load_demo_records, write_demo_files


class MockSource(OpportunitySource):
    def __init__(self, name: str = "demo", *, mutate: bool = False) -> None:
        self.name = name
        self.mutate = mutate

    async def fetch(self) -> list[RawOpportunityIn]:
        write_demo_files()
        records = load_demo_records(mutate=self.mutate)
        now = utcnow()
        payload: list[RawOpportunityIn] = []
        for item in records:
            payload.append(
                RawOpportunityIn(
                    source_name=self.name,
                    external_id=item.get("external_id"),
                    source_url=item.get("url"),
                    retrieved_at=now,
                    raw_title=item.get("title"),
                    raw_description=item.get("description"),
                    raw_organisation=item.get("organisation"),
                    raw_location=item.get("location"),
                    raw_value=item.get("value"),
                    raw_deadline=item.get("deadline"),
                    raw_category=item.get("category"),
                    raw_contact_name=item.get("contact_name"),
                    raw_contact_email=item.get("contact_email"),
                    raw_requirements=item.get("requirements"),
                    raw_skills=list(item.get("skills") or []),
                    raw_metadata=dict(item.get("metadata") or {}),
                    content_hash=content_hash_from_raw(
                        title=item.get("title"),
                        description=item.get("description"),
                        organisation=item.get("organisation"),
                        location=item.get("location"),
                        value=item.get("value"),
                        deadline=item.get("deadline"),
                        url=item.get("url"),
                        extra=item.get("metadata") or {},
                    ),
                )
            )
        return payload

    async def healthcheck(self) -> SourceHealth:
        return SourceHealth(name=self.name, healthy=True, message="bundled demo dataset available")
