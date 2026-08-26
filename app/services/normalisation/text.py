"""Text normalisation helpers."""

from __future__ import annotations

import html
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

_WHITESPACE = re.compile(r"\s+")
_ORG_NOISE = re.compile(
    r"\b(ltd|limited|llp|plc|inc|incorporated|llc|gmbh|cic|trust|authority|"
    r"council|group|services|partnership|consortium|institute|office)\b",
    re.IGNORECASE,
)


def collapse_whitespace(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = _WHITESPACE.sub(" ", value).strip()
    return cleaned or None


def strip_html(value: str | None) -> str | None:
    if value is None:
        return None
    unescaped = html.unescape(value)
    soup = BeautifulSoup(unescaped, "lxml")
    text = soup.get_text(separator=" ", strip=True)
    return collapse_whitespace(text)


def normalise_title(value: str | None) -> str | None:
    cleaned = collapse_whitespace(value)
    if cleaned is None:
        return None
    return cleaned.casefold()


def normalise_organisation(value: str | None) -> str | None:
    cleaned = collapse_whitespace(value)
    if cleaned is None:
        return None
    without_noise = _ORG_NOISE.sub(" ", cleaned)
    return collapse_whitespace(without_noise.casefold())


def canonical_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.netloc:
        return collapse_whitespace(value)
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid", "ref"}
    ]
    normalised = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower().removeprefix("www."),
        path=parsed.path.rstrip("/") or "/",
        query=urlencode(query),
        fragment="",
    )
    return urlunparse(normalised)


def extract_emails(value: str | None) -> list[str]:
    if not value:
        return []
    found = re.findall(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", value, flags=re.IGNORECASE)
    unique: list[str] = []
    for email in found:
        lowered = email.lower()
        if lowered not in unique:
            unique.append(lowered)
    return unique


def extract_keywords(text: str | None, *, limit: int = 12) -> list[str]:
    if not text:
        return []
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.casefold())
    stop = {
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
        "into",
        "are",
        "was",
        "were",
        "will",
        "shall",
        "must",
        "have",
        "has",
        "been",
        "including",
        "required",
        "support",
        "service",
        "services",
        "project",
        "please",
        "within",
        "using",
        "across",
        "their",
        "them",
        "such",
        "other",
        "than",
        "able",
        "work",
        "team",
        "role",
        "based",
    }
    counts: dict[str, int] = {}
    for token in tokens:
        if token in stop:
            continue
        counts[token] = counts.get(token, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [word for word, _ in ranked[:limit]]


def summarise(text: str | None, *, limit: int = 400) -> str | None:
    cleaned = strip_html(text) or collapse_whitespace(text)
    if not cleaned:
        return None
    if len(cleaned) <= limit:
        return cleaned
    truncated = cleaned[: limit - 1].rsplit(" ", 1)[0]
    return truncated + "…"
