"""HTTP client retry and error categorisation tests."""

from __future__ import annotations

import httpx
import pytest
import respx
from app.core.exceptions import ConfigurationError, SourceHttpError, SourceRateLimitError
from app.sources.http_client import ResponsibleHttpClient
from app.sources.registry import load_sources_file


@pytest.mark.asyncio
@respx.mock
async def test_http_500_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.sources.http_client.robots_allows", lambda *args, **kwargs: True)
    respx.get("https://example.invalid/feed").mock(return_value=httpx.Response(500, text="nope"))
    client = ResponsibleHttpClient(source_name="test")
    client.settings.request_max_retries = 2
    client.settings.request_delay_seconds = 0
    client.settings.respect_robots_txt = False
    with pytest.raises(SourceHttpError):
        await client.get("https://example.invalid/feed", respect_robots=False)
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_http_429_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    respx.get("https://example.invalid/limited").mock(
        return_value=httpx.Response(429, text="slow down")
    )
    client = ResponsibleHttpClient(source_name="test")
    client.settings.request_max_retries = 2
    client.settings.request_delay_seconds = 0
    with pytest.raises(SourceRateLimitError):
        await client.get("https://example.invalid/limited", respect_robots=False)
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_retry_exhaustion() -> None:
    route = respx.get("https://example.invalid/flaky").mock(return_value=httpx.Response(500))
    client = ResponsibleHttpClient(source_name="test")
    client.settings.request_max_retries = 3
    client.settings.request_delay_seconds = 0
    with pytest.raises(SourceHttpError):
        await client.get("https://example.invalid/flaky", respect_robots=False)
    assert route.call_count == 3
    await client.aclose()


def test_invalid_source_configuration(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "sources.yaml"
    path.write_text("sources: {}\n", encoding="utf-8")
    from app.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    settings.__dict__["sources_config_path"] = path
    with pytest.raises(ConfigurationError):
        load_sources_file(path)
