"""UK-centric location and country normalisation."""

from __future__ import annotations

from app.services.normalisation.text import collapse_whitespace

_COUNTRY_ALIASES = {
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "u.k": "United Kingdom",
    "united kingdom": "United Kingdom",
    "great britain": "United Kingdom",
    "gb": "United Kingdom",
    "england": "United Kingdom",
    "scotland": "United Kingdom",
    "wales": "United Kingdom",
    "northern ireland": "United Kingdom",
    "usa": "United States",
    "u.s.a.": "United States",
    "united states": "United States",
    "united states of america": "United States",
    "ireland": "Ireland",
    "republic of ireland": "Ireland",
}

_UK_LOCATIONS = {
    "london": "London",
    "manchester": "Manchester",
    "birmingham": "Birmingham",
    "leeds": "Leeds",
    "glasgow": "Glasgow",
    "edinburgh": "Edinburgh",
    "bristol": "Bristol",
    "cardiff": "Cardiff",
    "belfast": "Belfast",
    "liverpool": "Liverpool",
    "newcastle": "Newcastle upon Tyne",
    "sheffield": "Sheffield",
    "nottingham": "Nottingham",
    "cambridge": "Cambridge",
    "oxford": "Oxford",
    "reading": "Reading",
    "brighton": "Brighton",
    "remote": "Remote",
    "uk-wide": "UK-wide",
    "nationwide": "UK-wide",
    "united kingdom": "United Kingdom",
}


def normalise_location(value: str | None) -> tuple[str | None, str | None, bool]:
    """Return (location, country, is_remote)."""

    cleaned = collapse_whitespace(value)
    if not cleaned:
        return None, None, False
    lowered = cleaned.casefold()
    is_remote = "remote" in lowered
    country = None
    for alias, canonical in _COUNTRY_ALIASES.items():
        if alias in lowered:
            country = canonical
            break
    location = None
    for alias, canonical in _UK_LOCATIONS.items():
        if alias in lowered:
            location = canonical
            break
    if location is None:
        location = cleaned
    if country is None and location in set(_UK_LOCATIONS.values()):
        country = "United Kingdom"
    return location, country, is_remote
