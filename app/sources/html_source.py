"""Public HTML listing connector using BeautifulSoup. No anti-bot behaviour."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from app.core.config import PROJECT_ROOT
from app.core.exceptions import SourceError
from app.schemas.raw import RawOpportunityIn, SourceHealth
from app.services.deduplication.fingerprint import content_hash_from_raw
from app.services.normalisation.dates import utcnow
from app.services.normalisation.text import collapse_whitespace
from app.sources.base import OpportunitySource
from app.sources.http_client import http_client


def _text(node: object | None) -> str | None:
    if node is None:
        return None
    get_text = getattr(node, "get_text", None)
    if callable(get_text):
        return collapse_whitespace(get_text())
    return collapse_whitespace(str(node))


class PublicHTMLSource(OpportunitySource):
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
            raise SourceError("HTML source requires a url or path", details={"source": self.name})
        async with http_client(self.name) as client:
            response = await client.get(self.url)
            return response.text

    async def fetch(self) -> list[RawOpportunityIn]:
        soup = BeautifulSoup(await self._load(), "lxml")
        now = utcnow()
        records: list[RawOpportunityIn] = []
        articles = soup.select("article.opportunity") or soup.select("article") or soup.select("li")
        for article in articles:
            heading = article.find(["h1", "h2", "h3"])
            anchor = article.find("a")
            title = _text(heading) or _text(anchor)
            href = anchor.get("href") if anchor else None
            url = href if isinstance(href, str) else None
            org = _text(article.select_one(".org"))
            desc = _text(article.select_one(".desc"))
            meta = _text(article.select_one(".meta"))
            if not title:
                continue
            records.append(
                RawOpportunityIn(
                    source_name=self.name,
                    source_url=url,
                    retrieved_at=now,
                    raw_title=title,
                    raw_description=desc,
                    raw_organisation=org,
                    raw_value=meta,
                    raw_metadata={"html_meta": meta},
                    content_hash=content_hash_from_raw(
                        title=title,
                        description=desc,
                        organisation=org,
                        location=None,
                        value=meta,
                        deadline=None,
                        url=url,
                    ),
                )
            )
        return records

    async def healthcheck(self) -> SourceHealth:
        path = self._resolved_path()
        if path is not None:
            return SourceHealth(name=self.name, healthy=path.exists(), message="local html file")
        try:
            await self._load()
            return SourceHealth(name=self.name, healthy=True)
        except Exception as exc:  # noqa: BLE001
            return SourceHealth(name=self.name, healthy=False, message=str(exc))
