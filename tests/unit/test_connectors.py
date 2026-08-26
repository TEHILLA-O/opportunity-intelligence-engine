"""JSON / RSS / HTML connector tests against bundled fixtures."""

from __future__ import annotations

import pytest
from app.sources.demo_dataset import write_demo_files
from app.sources.html_source import PublicHTMLSource
from app.sources.json_source import JSONSource
from app.sources.rss_source import RSSSource


@pytest.mark.asyncio
async def test_local_connectors_parse_bundled_files() -> None:
    write_demo_files()
    json_records = await JSONSource("sample_json", path="data/demo/sample_feed.json").fetch()
    rss_records = await RSSSource("sample_rss", path="data/demo/sample_feed.rss").fetch()
    html_records = await PublicHTMLSource(
        "sample_html", path="data/demo/sample_listing.html"
    ).fetch()
    assert json_records
    assert rss_records
    assert html_records
    assert json_records[0].raw_title
    assert rss_records[0].source_url
    assert html_records[0].raw_title
