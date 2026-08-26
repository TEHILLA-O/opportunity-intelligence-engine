"""Deterministic currency and monetary-range parsing."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from app.core.exceptions import NormalisationError

_CURRENCY_SYMBOLS = {
    "£": "GBP",
    "$": "USD",
    "€": "EUR",
}
_CURRENCY_WORDS = {
    "gbp": "GBP",
    "pound": "GBP",
    "pounds": "GBP",
    "sterling": "GBP",
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
}

_NUMBER = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
_RANGE = re.compile(
    rf"(?P<cur1>£|\$|€|GBP|USD|EUR)?\s*(?P<min>{_NUMBER})\s*"
    rf"(?:-|–|to)\s*(?P<cur2>£|\$|€|GBP|USD|EUR)?\s*(?P<max>{_NUMBER})",
    re.IGNORECASE,
)
_SINGLE = re.compile(rf"(?P<cur>£|\$|€|GBP|USD|EUR)?\s*(?P<val>{_NUMBER})", re.IGNORECASE)
_ISO = re.compile(r"\b(GBP|USD|EUR)\b", re.IGNORECASE)


def _to_decimal(raw: str) -> Decimal:
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation as exc:
        raise NormalisationError(f"Cannot parse monetary amount: {raw}") from exc


def _currency_from_token(token: str | None) -> str | None:
    if not token:
        return None
    if token in _CURRENCY_SYMBOLS:
        return _CURRENCY_SYMBOLS[token]
    return _CURRENCY_WORDS.get(token.lower()) or (token.upper() if len(token) == 3 else None)


def parse_currency_code(value: str | None) -> str | None:
    if not value:
        return None
    stripped = value.strip()
    if stripped in _CURRENCY_SYMBOLS:
        return _CURRENCY_SYMBOLS[stripped]
    match = _ISO.search(stripped)
    if match:
        return match.group(1).upper()
    for symbol, code in _CURRENCY_SYMBOLS.items():
        if symbol in stripped:
            return code
    lowered = stripped.lower()
    for word, code in _CURRENCY_WORDS.items():
        if word in lowered:
            return code
    if len(stripped) == 3 and stripped.isalpha():
        return stripped.upper()
    return None


def parse_money(
    value: str | None,
) -> tuple[Decimal | None, Decimal | None, Decimal | None, str | None]:
    """Return (minimum, maximum, estimated, currency) from a free-text amount.

    Malformed input returns (None, None, None, currency_if_any) rather than raising,
    so a single bad value cannot abort a source batch.
    """

    if not value or not str(value).strip():
        return None, None, None, None
    text = str(value).strip()
    currency = parse_currency_code(text)
    try:
        ranged = _RANGE.search(text)
        if ranged:
            minimum = _to_decimal(ranged.group("min"))
            maximum = _to_decimal(ranged.group("max"))
            if minimum > maximum:
                minimum, maximum = maximum, minimum
            estimated = (minimum + maximum) / Decimal("2")
            currency = (
                _currency_from_token(ranged.group("cur1"))
                or _currency_from_token(ranged.group("cur2"))
                or currency
            )
            return minimum, maximum, estimated, currency
        single = _SINGLE.search(text)
        if not single:
            return None, None, None, currency
        amount = _to_decimal(single.group("val"))
        currency = _currency_from_token(single.group("cur")) or currency
        return amount, amount, amount, currency
    except NormalisationError:
        return None, None, None, currency
