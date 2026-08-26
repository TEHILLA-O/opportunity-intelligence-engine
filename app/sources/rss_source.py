"""RSS/Atom connector."""

from __future__ import annotations

from pathlib import Path

import feedparser

from app.core.config import PROJECT_ROOT
from app.core.exceptions import SourceError
from app.schemas.raw import RawOpportunityIn, SourceHealth
from app.services.deduplication.fingerprint import content_hash_from_raw
from app.services.normalisation.dates import utcnow
from app.sources.base import OpportunitySource
from app.sources.http_client import http_client


class RSSSource(OpportunitySource):
    def __init__(self, name: str, *, url: str | None = None, path: str | None = None) -> None:
        self.name = name
        self.url = url
        self.path = Path(path) if path else None

    def _resolved_path(self) -> Path | None:
        if self.path is None:
            return None
        return self.path if self.path.is_absolute() else PROJECT_ROOT / self.path

    async def _load(self) -> str:
        path = self._resolved_path()
        if path is not None:
            return path.read_text(encoding="utf-8")
        if not self.url:
            raise SourceError("RSS source requires a url or path", details={"source": self.name})
        async with http_client(self.name) as client:
            response = await client.get(self.url)
            return response.text

    async def fetch(self) -> list[RawOpportunityIn]:
        parsed = feedparser.parse(await self._load())
        now = utcnow()
        records: list[RawOpportunityIn] = []
        for entry in parsed.entries:
            title = getattr(entry, "title", None)
            link = getattr(entry, "link", None)
            summary = getattr(entry, "summary", None) or getattr(entry, "description", None)
            org = getattr(entry, "author", None)
            guid = getattr(entry, "id", None) or getattr(entry, "guid", None)
            records.append(
                RawOpportunityIn(
                    source_name=self.name,
                    external_id=str(guid) if guid else None,
                    source_url=link,
                    retrieved_at=now,
                    raw_title=title,
                    raw_description=summary,
                    raw_organisation=org,
                    raw_metadata={"rss": True, "title_detail": getattr(entry, "title_detail", {})},
                    content_hash=content_hash_from_raw(
                        title=title,
                        description=summary,
                        organisation=org,
                        location=None,
                        value=None,
                        deadline=None,
                        url=link,
                    ),
                )
            )
        return records

    async def healthcheck(self) -> SourceHealth:
        path = self._resolved_path()
        if path is not None:
            return SourceHealth(name=self.name, healthy=path.exists(), message="local rss file")
        try:
            await self._load()
            return SourceHealth(name=self.name, healthy=True)
        except Exception as exc:  # noqa: BLE001
            return SourceHealth(name=self.name, healthy=False, message=str(exc))
