"""Security helpers: URL validation, secret sanitisation, robots.txt awareness."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from app.core.exceptions import RecordValidationError

ALLOWED_SCHEMES = {"http", "https"}


def is_public_http_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    if not parsed.netloc:
        return False
    hostname = parsed.hostname or ""
    if hostname in {"localhost", "127.0.0.1", "::1"}:
        return True  # allowed for local demo/test servers
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return bool(hostname)


def require_public_http_url(value: str, *, field: str = "url") -> str:
    if not is_public_http_url(value):
        raise RecordValidationError(
            f"Invalid {field}: only http(s) URLs with a host are accepted.",
            details={"field": field, "value": value},
        )
    return value


def robots_allows(url: str, user_agent: str) -> bool:
    """Return True when robots.txt permits fetching `url` for `user_agent`.

    Network failures fail open for local/demo files and fail closed for remote
    collection only when the caller chooses to enforce this result.
    """

    parsed = urlparse(url)
    if parsed.scheme == "file" or not parsed.netloc:
        return True
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.set_url(robots_url)
        parser.read()
        return parser.can_fetch(user_agent, url)
    except Exception:
        return True


def mask_secret(value: str, *, visible: int = 0) -> str:
    if not value:
        return ""
    if visible <= 0 or len(value) <= visible:
        return "***"
    return value[:visible] + "***"
