"""Multi-signal duplicate detection."""

from __future__ import annotations

from decimal import Decimal

from rapidfuzz import fuzz

from app.core.constants import (
    AMBIGUOUS_DUPLICATE_THRESHOLD,
    CONFIRMED_DUPLICATE_THRESHOLD,
    EXACT_MATCH_CONFIDENCE,
)
from app.core.enums import DuplicateStatus
from app.db.models.opportunity import Opportunity
from app.schemas.opportunity import NormalisedOpportunity
from app.services.normalisation.dates import ensure_utc
from app.services.normalisation.text import canonical_url, normalise_organisation, normalise_title


class DuplicateDecision:
    def __init__(
        self,
        *,
        duplicate: bool,
        confidence: Decimal,
        status: DuplicateStatus,
        signals: dict[str, object],
        matched: Opportunity | None = None,
        reason: str,
    ) -> None:
        self.duplicate = duplicate
        self.confidence = confidence
        self.status = status
        self.signals = signals
        self.matched = matched
        self.reason = reason

    def as_dict(self) -> dict[str, object]:
        return {
            "duplicate": self.duplicate,
            "confidence": float(self.confidence),
            "status": self.status.value,
            "signals": self.signals,
            "reason": self.reason,
            "matched_id": str(self.matched.id) if self.matched else None,
        }


class DeduplicationEngine:
    def compare(
        self,
        incoming: NormalisedOpportunity,
        existing: Opportunity,
        *,
        same_source: bool,
    ) -> DuplicateDecision:
        signals: dict[str, object] = {}
        reasons: list[str] = []
        confidence = Decimal("0")

        if (
            same_source
            and incoming.external_id
            and existing.external_id
            and incoming.external_id == existing.external_id
        ):
            signals["exact_source_id"] = True
            return DuplicateDecision(
                duplicate=True,
                confidence=EXACT_MATCH_CONFIDENCE,
                status=DuplicateStatus.CONFIRMED,
                signals=signals,
                matched=existing,
                reason="exact source ID",
            )

        incoming_url = incoming.canonical_url or canonical_url(incoming.source_url)
        if incoming_url and existing.canonical_url and incoming_url == existing.canonical_url:
            signals["canonical_url"] = True
            return DuplicateDecision(
                duplicate=True,
                confidence=EXACT_MATCH_CONFIDENCE,
                status=DuplicateStatus.CONFIRMED,
                signals=signals,
                matched=existing,
                reason="canonical source URL",
            )

        if incoming.content_hash and incoming.content_hash == existing.content_hash:
            signals["content_fingerprint"] = True
            return DuplicateDecision(
                duplicate=True,
                confidence=EXACT_MATCH_CONFIDENCE,
                status=DuplicateStatus.CONFIRMED,
                signals=signals,
                matched=existing,
                reason="content fingerprint",
            )

        title_a = incoming.normalised_title or normalise_title(incoming.title) or ""
        title_b = existing.normalised_title or normalise_title(existing.title) or ""
        org_a = (
            incoming.normalised_organisation or normalise_organisation(incoming.organisation) or ""
        )
        org_b = (
            existing.normalised_organisation or normalise_organisation(existing.organisation) or ""
        )

        title_ratio = fuzz.token_sort_ratio(title_a, title_b) / 100 if title_a and title_b else 0.0
        org_ratio = fuzz.token_sort_ratio(org_a, org_b) / 100 if org_a and org_b else 0.0
        org_match = bool(org_a and org_b and org_ratio >= 0.9)
        signals["title_similarity"] = round(title_ratio, 4)
        signals["organisation_similarity"] = round(org_ratio, 4)
        signals["organisation_match"] = org_match

        deadline_match = False
        incoming_deadline = ensure_utc(incoming.deadline_at)
        existing_deadline = ensure_utc(existing.deadline_at)
        if incoming_deadline and existing_deadline:
            delta_hours = abs((incoming_deadline - existing_deadline).total_seconds()) / 3600
            deadline_match = delta_hours <= 24
        signals["deadline_match"] = deadline_match

        if title_a and title_b and title_a == title_b and org_match:
            return DuplicateDecision(
                duplicate=True,
                confidence=Decimal("0.96"),
                status=DuplicateStatus.CONFIRMED,
                signals=signals,
                matched=existing,
                reason="normalised title + organisation",
            )

        weighted = Decimal(
            str(round(title_ratio * 0.6 + org_ratio * 0.3 + (0.1 if deadline_match else 0), 4))
        )
        confidence = weighted
        if title_ratio >= 0.92 and org_match:
            reasons.append("very similar title and matching organisation")
            return DuplicateDecision(
                duplicate=True,
                confidence=max(confidence, Decimal("0.90")),
                status=DuplicateStatus.CONFIRMED,
                signals=signals,
                matched=existing,
                reason="; ".join(reasons) or "fuzzy title similarity",
            )
        if confidence >= CONFIRMED_DUPLICATE_THRESHOLD and org_match:
            return DuplicateDecision(
                duplicate=True,
                confidence=confidence,
                status=DuplicateStatus.CONFIRMED,
                signals=signals,
                matched=existing,
                reason="fuzzy title similarity",
            )
        if confidence >= AMBIGUOUS_DUPLICATE_THRESHOLD:
            return DuplicateDecision(
                duplicate=False,
                confidence=confidence,
                status=DuplicateStatus.AMBIGUOUS,
                signals=signals,
                matched=existing,
                reason="borderline similarity — not auto-merged",
            )
        return DuplicateDecision(
            duplicate=False,
            confidence=confidence,
            status=DuplicateStatus.REJECTED,
            signals=signals,
            matched=None,
            reason="insufficient similarity",
        )
