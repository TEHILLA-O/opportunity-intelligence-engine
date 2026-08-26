"""Application settings loaded from environment variables and optional .env file."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _is_vercel() -> bool:
    return bool(os.environ.get("VERCEL"))


def _vercel_tmp() -> Path:
    return Path("/tmp/opportunity-engine")


def sqlite_database_url(path: Path) -> str:
    """Build a SQLAlchemy SQLite URL for an absolute filesystem path."""
    resolved = path.resolve()
    return f"sqlite+aiosqlite:///{resolved.as_posix()}"


class Settings(BaseSettings):
    """Runtime configuration. Optional credentials are never required for local/demo use."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_debug: bool = False
    app_name: str = "Opportunity Engine"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    secret_key: SecretStr = SecretStr("change-me-in-production")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "sqlite+aiosqlite:///./data/opportunity_engine.db"

    request_timeout: float = 20.0
    request_max_retries: int = 3
    request_rate_limit: float = 1.0
    request_delay_seconds: float = 0.5
    user_agent: str = "OpportunityEngine/0.1 (+https://example.local/bot; responsible-automation)"
    respect_robots_txt: bool = True

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_from: str = "alerts@localhost"
    smtp_use_tls: bool = True

    webhook_url: str = ""
    enrichment_provider: str = "none"
    prefect_api_url: str = ""

    sources_config_path: Path = Field(default=PROJECT_ROOT / "config" / "sources.yaml")
    scoring_config_path: Path = Field(default=PROJECT_ROOT / "config" / "scoring.yaml")
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    demo_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "demo")
    exports_dir: Path = Field(default=PROJECT_ROOT / "data" / "exports")
    raw_dir: Path = Field(default=PROJECT_ROOT / "data" / "raw")

    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host)

    @property
    def webhook_enabled(self) -> bool:
        return bool(self.webhook_url)

    def ensure_data_dirs(self) -> None:
        for path in (self.data_dir, self.demo_data_dir, self.exports_dir, self.raw_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    overrides: dict[str, object] = {}
    if _is_vercel():
        tmp = _vercel_tmp()
        tmp.mkdir(parents=True, exist_ok=True)
        db_file = tmp / "opportunity_engine.db"
        env_db = os.environ.get("DATABASE_URL", "")
        if env_db.startswith("postgresql"):
            database_url = env_db
        else:
            database_url = sqlite_database_url(db_file)
        overrides.update(
            {
                "app_env": "production",
                "database_url": database_url,
                "data_dir": tmp / "data",
                "demo_data_dir": tmp / "data" / "demo",
                "exports_dir": tmp / "data" / "exports",
                "raw_dir": tmp / "data" / "raw",
            }
        )
    settings = Settings(**overrides)
    settings.ensure_data_dirs()
    return settings
