"""Source registry: configuration loading and connector construction."""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.config import get_settings
from app.core.enums import SourceType
from app.core.exceptions import ConfigurationError
from app.schemas.config import SourceConfig, SourcesFile
from app.sources.base import OpportunitySource
from app.sources.html_source import PublicHTMLSource
from app.sources.json_source import JSONSource
from app.sources.mock_source import MockSource
from app.sources.playwright_source import PlaywrightSource
from app.sources.rss_source import RSSSource


def load_sources_file(path: Path | None = None) -> SourcesFile:
    config_path = path or get_settings().sources_config_path
    if not config_path.exists():
        raise ConfigurationError(f"Source configuration not found: {config_path}")
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    try:
        return SourcesFile.model_validate(payload)
    except Exception as exc:
        raise ConfigurationError(f"Invalid source configuration: {exc}") from exc


def build_source(
    name: str, config: SourceConfig, *, mutate_demo: bool = False
) -> OpportunitySource:
    if config.type == SourceType.MOCK:
        return MockSource(name=name, mutate=mutate_demo)
    if config.type == SourceType.JSON:
        return JSONSource(name=name, url=config.url, path=config.path)
    if config.type == SourceType.RSS:
        return RSSSource(name=name, url=config.url, path=config.path)
    if config.type == SourceType.HTML:
        return PublicHTMLSource(name=name, url=config.url, path=config.path)
    if config.type == SourceType.PLAYWRIGHT:
        return PlaywrightSource(name=name, url=config.url)
    raise ConfigurationError(f"Unsupported source type: {config.type}")


def enabled_sources(
    *,
    only: str | None = None,
    mutate_demo: bool = False,
    path: Path | None = None,
) -> list[tuple[str, SourceConfig, OpportunitySource]]:
    file = load_sources_file(path)
    selected: list[tuple[str, SourceConfig, OpportunitySource]] = []
    for name, config in file.sources.items():
        if only and name != only:
            continue
        if not config.enabled and name != only:
            continue
        selected.append((name, config, build_source(name, config, mutate_demo=mutate_demo)))
    if only and not selected:
        raise ConfigurationError(f"Unknown or disabled source: {only}")
    return selected
