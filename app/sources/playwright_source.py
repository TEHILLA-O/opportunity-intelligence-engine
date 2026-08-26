"""Optional Playwright connector. Disabled unless explicitly configured.

This adapter fetches publicly available pages. It does not bypass CAPTCHAs,
authentication, paywalls or bot protections.
"""

from __future__ import annotations

from app.core.exceptions import SourceError
from app.schemas.raw import RawOpportunityIn, SourceHealth
from app.services.deduplication.fingerprint import content_hash_from_raw
from app.services.normalisation.dates import utcnow
from app.sources.base import OpportunitySource


class PlaywrightSource(OpportunitySource):
    def __init__(self, name: str, *, url: str | None = None, selector: str = "article") -> None:
        self.name = name
        self.url = url
        self.selector = selector

    async def fetch(self) -> list[RawOpportunityIn]:
        if not self.url:
            raise SourceError("Playwright source requires a url", details={"source": self.name})
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:
            raise SourceError(
                "Playwright is not installed. Install the optional extra: uv sync --extra playwright",
                details={"source": self.name},
            ) from exc

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(self.url, wait_until="domcontentloaded", timeout=20000)
            elements = await page.locator(self.selector).all_text_contents()
            await browser.close()

        now = utcnow()
        records: list[RawOpportunityIn] = []
        for index, text in enumerate(elements, start=1):
            title = text.strip().split("\n", 1)[0][:200]
            if not title:
                continue
            records.append(
                RawOpportunityIn(
                    source_name=self.name,
                    external_id=f"{self.name}-{index}",
                    source_url=self.url,
                    retrieved_at=now,
                    raw_title=title,
                    raw_description=text.strip(),
                    content_hash=content_hash_from_raw(
                        title=title,
                        description=text,
                        organisation=None,
                        location=None,
                        value=None,
                        deadline=None,
                        url=self.url,
                    ),
                )
            )
        return records

    async def healthcheck(self) -> SourceHealth:
        if not self.url:
            return SourceHealth(name=self.name, healthy=False, message="no url configured")
        return SourceHealth(
            name=self.name,
            healthy=True,
            message="Playwright adapter configured (optional extra)",
        )
