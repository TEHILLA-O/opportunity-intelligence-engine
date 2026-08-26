"""JSON file or HTTP JSON feed connector."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import PROJECT_ROOT
from app.core.exceptions import SourceError
from app.schemas.raw import RawOpportunityIn, SourceHealth
from app.services.deduplication.fingerprint import content_hash_from_raw
from app.services.normalisation.dates import utcnow
from app.sources.base import OpportunitySource
from app.sources.http_client import http_client


def _coerce_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "opportunities", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    raise SourceError("JSON payload is not a list or object containing items")


class JSONSource(OpportunitySource):
    def __init__(self, name: str, *, url: str | None = None, path: str | None = None) -> None:
        self.name = name
        self.url = url
        self.path = Path(path) if path else None

    def _resolved_path(self) -> Path | None:
        if self.path is None:
            return None
        if self.path.is_absolute():
            return self.path
        return PROJECT_ROOT / self.path

    async def fetch(self) -> list[RawOpportunityIn]:
        path = self._resolved_path()
        if path is not None:
            text = path.read_text(encoding="utf-8")
            status = 200
        elif self.url:
            async with http_client(self.name) as client:
                response = await client.get(self.url)
                text = response.text
                status = response.status_code
        else:
            raise SourceError("JSON source requires a url or path", details={"source": self.name})
        items = _coerce_items(json.loads(text))
        now = utcnow()
        records: list[RawOpportunityIn] = []
        for item in items:
            title = item.get("title") or item.get("name")
            url = item.get("url") or item.get("link") or item.get("source_url")
            records.append(
                RawOpportunityIn(
                    source_name=self.name,
                    external_id=str(item.get("external_id") or item.get("id") or "") or None,
                    source_url=url,
                    retrieved_at=now,
                    raw_title=title,
                    raw_description=item.get("description") or item.get("summary"),
                    raw_organisation=item.get("organisation")
                    or item.get("organization")
                    or item.get("buyer"),
                    raw_location=item.get("location"),
                    raw_value=str(item["value"])
                    if item.get("value") is not None
                    else item.get("budget"),
                    raw_deadline=str(item["deadline"])
                    if item.get("deadline") is not None
                    else None,
                    raw_category=item.get("category"),
                    raw_contact_name=item.get("contact_name"),
                    raw_contact_email=item.get("contact_email"),
                    raw_requirements=item.get("requirements"),
                    raw_skills=list(item.get("skills") or []),
                    raw_metadata=item,
                    http_status=status,
                    content_hash=content_hash_from_raw(
                        title=title,
                        description=item.get("description"),
                        organisation=item.get("organisation"),
                        location=item.get("location"),
                        value=str(item.get("value") or ""),
                        deadline=str(item.get("deadline") or ""),
                        url=url,
                        extra=item,
                    ),
                )
            )
        return records

    async def healthcheck(self) -> SourceHealth:
        path = self._resolved_path()
        if path is not None:
            exists = path.exists()
            return SourceHealth(
                name=self.name,
                healthy=exists,
                message="file available" if exists else "file missing",
            )
        if not self.url:
            return SourceHealth(name=self.name, healthy=False, message="no url or path configured")
        try:
            async with http_client(self.name) as client:
                response = await client.get(self.url)
            return SourceHealth(
                name=self.name,
                healthy=response.status_code < 400,
                status_code=response.status_code,
            )
        except Exception as exc:  # noqa: BLE001 — healthcheck must never raise
            return SourceHealth(name=self.name, healthy=False, message=str(exc))
