"""Shared HTTP client with timeouts, retries, rate limits and robots awareness."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import Settings, get_settings
from app.core.exceptions import SourceHttpError, SourceRateLimitError, SourceTimeoutError
from app.core.security import robots_allows


class RateLimiter:
    def __init__(self, rate_per_second: float) -> None:
        self._interval = 1.0 / max(rate_per_second, 0.01)
        self._lock = asyncio.Lock()
        self._last = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            loop = asyncio.get_running_loop()
            now = loop.time()
            wait_for = self._last + self._interval - now
            if wait_for > 0:
                await asyncio.sleep(wait_for)
            self._last = loop.time()


class ResponsibleHttpClient:
    def __init__(self, settings: Settings | None = None, *, source_name: str = "http") -> None:
        self.settings = settings or get_settings()
        self.source_name = source_name
        self.limiter = RateLimiter(self.settings.request_rate_limit)
        self._client = httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            headers={"User-Agent": self.settings.user_agent},
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, url: str, *, respect_robots: bool | None = None) -> httpx.Response:
        enforce = self.settings.respect_robots_txt if respect_robots is None else respect_robots
        if enforce and url.startswith(("http://", "https://")):
            if not robots_allows(url, self.settings.user_agent):
                raise SourceHttpError(
                    "robots.txt disallows this URL",
                    source=self.source_name,
                    status_code=None,
                    details={"url": url},
                )
        await self.limiter.acquire()
        if self.settings.request_delay_seconds:
            await asyncio.sleep(self.settings.request_delay_seconds)
        try:
            return await self._get_with_retry(url)
        except RetryError as exc:
            last = exc.last_attempt.exception()
            if isinstance(last, httpx.TimeoutException):
                raise SourceTimeoutError(
                    f"Timed out fetching {url}",
                    source=self.source_name,
                    details={"url": url},
                ) from exc
            if isinstance(last, SourceRateLimitError | SourceHttpError | SourceTimeoutError):
                raise last from exc
            raise SourceHttpError(
                f"Failed fetching {url}: {last}",
                source=self.source_name,
                details={"url": url},
            ) from exc

    def _retry(self) -> Any:
        return retry(
            stop=stop_after_attempt(self.settings.request_max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=8),
            retry=retry_if_exception_type(
                (httpx.TimeoutException, SourceRateLimitError, SourceHttpError)
            ),
            reraise=True,
        )

    async def _get_with_retry(self, url: str) -> httpx.Response:
        @self._retry()
        async def _inner() -> httpx.Response:
            try:
                response = await self._client.get(url)
            except httpx.TimeoutException as exc:
                raise SourceTimeoutError(
                    f"Timed out fetching {url}",
                    source=self.source_name,
                    details={"url": url},
                ) from exc
            if response.status_code == 429:
                raise SourceRateLimitError(
                    f"HTTP 429 from {url}",
                    source=self.source_name,
                    details={"url": url, "status": 429},
                )
            if response.status_code >= 500:
                raise SourceHttpError(
                    f"HTTP {response.status_code} from {url}",
                    source=self.source_name,
                    status_code=response.status_code,
                    details={"url": url},
                )
            if response.status_code >= 400:
                raise SourceHttpError(
                    f"HTTP {response.status_code} from {url}",
                    source=self.source_name,
                    status_code=response.status_code,
                    details={"url": url},
                )
            return response

        return await _inner()


@asynccontextmanager
async def http_client(source_name: str) -> AsyncIterator[ResponsibleHttpClient]:
    client = ResponsibleHttpClient(source_name=source_name)
    try:
        yield client
    finally:
        await client.aclose()
