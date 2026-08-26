"""Content hashing and identity fingerprints."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.core.constants import CONTENT_HASH_ALGORITHM
from app.services.normalisation.text import canonical_url, normalise_organisation, normalise_title


def sha256_text(*parts: str | None) -> str:
    payload = "\n".join(part or "" for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def content_hash_from_raw(
    *,
    title: str | None,
    description: str | None,
    organisation: str | None,
    location: str | None,
    value: str | None,
    deadline: str | None,
    url: str | None,
    extra: dict[str, Any] | None = None,
) -> str:
    serialised_extra = json.dumps(extra or {}, sort_keys=True, default=str)
    return sha256_text(
        title, description, organisation, location, value, deadline, url, serialised_extra
    )


def identity_fingerprint(
    *,
    title: str | None,
    organisation: str | None,
    canonical: str | None = None,
) -> str:
    return sha256_text(
        normalise_title(title),
        normalise_organisation(organisation),
        canonical_url(canonical),
    )


def hash_algorithm() -> str:
    return CONTENT_HASH_ALGORITHM
