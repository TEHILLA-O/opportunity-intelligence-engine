"""Deterministic, explainable opportunity scoring."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import yaml

from app.core.config import get_settings
from app.core.constants import RATING_HIGH, RATING_LOW, RATING_MEDIUM, RATING_VERY_HIGH
from app.core.enums import RemoteStatus, ScoreRating
from app.schemas.config import ScoringConfig, ScoringFile
from app.schemas.opportunity import NormalisedOpportunity, ScoredOpportunity
from app.services.deadlines.engine import DeadlineEngine


def rating_for_score(score: int) -> ScoreRating:
    if score >= RATING_VERY_HIGH:
        return ScoreRating.VERY_HIGH
    if score >= RATING_HIGH:
        return ScoreRating.HIGH
    if score >= RATING_MEDIUM:
        return ScoreRating.MEDIUM
    if score >= RATING_LOW:
        return ScoreRating.LOW
    return ScoreRating.VERY_LOW


def load_scoring_config(path: Path | None = None) -> ScoringConfig:
    config_path = path or get_settings().scoring_config_path
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return ScoringFile.model_validate(payload).scoring


class ScoringEngine:
    def __init__(self, config: ScoringConfig | None = None) -> None:
        self.config = config or load_scoring_config()
        self.deadlines = DeadlineEngine()

    def score(self, record: NormalisedOpportunity) -> ScoredOpportunity:
        reasons: list[str] = []
        total = 0
        haystack = " ".join(
            part
            for part in (
                record.title,
                record.description,
                record.requirements,
                " ".join(record.skills),
                " ".join(record.keywords),
                record.category or "",
            )
            if part
        ).casefold()

        for keyword, weight in self.config.keywords.items():
            if keyword.casefold() in haystack:
                total += weight
                reasons.append(f"{keyword} keyword match: {weight:+d}")

        for keyword, weight in self.config.excluded_keywords.items():
            if keyword.casefold() in haystack:
                total += weight
                reasons.append(f"excluded keyword '{keyword}': {weight:+d}")

        contract_bonus = self.config.preferred_contract_types.get(record.contract_type)
        if contract_bonus:
            total += contract_bonus
            reasons.append(f"Preferred contract type ({record.contract_type}): {contract_bonus:+d}")

        if record.category:
            category_key = record.category.casefold().replace(" ", "-")
            cat_bonus = self.config.preferred_categories.get(
                category_key
            ) or self.config.preferred_categories.get(record.category.casefold())
            if cat_bonus:
                total += cat_bonus
                reasons.append(f"Preferred category ({record.category}): {cat_bonus:+d}")

        location_blob = " ".join(filter(None, [record.location, record.country])).casefold()
        for place, bonus in self.config.preferred_locations.items():
            if place.casefold() in location_blob:
                total += bonus
                reasons.append(f"Preferred location ({place}): {bonus:+d}")
                break

        proc_bonus = self.config.preferred_procurement_types.get(record.procurement_type)
        if proc_bonus:
            total += proc_bonus
            reasons.append(
                f"Preferred procurement type ({record.procurement_type}): {proc_bonus:+d}"
            )

        skill_blob = " ".join(record.skills).casefold() + " " + haystack
        for skill, bonus in self.config.required_skills.items():
            if skill.casefold() in skill_blob:
                total += bonus
                reasons.append(f"Required skill match ({skill}): {bonus:+d}")

        if record.remote_status == RemoteStatus.REMOTE:
            total += self.config.remote_bonus
            reasons.append(f"Remote opportunity: {self.config.remote_bonus:+d}")
        elif record.remote_status == RemoteStatus.HYBRID:
            total += self.config.hybrid_bonus
            reasons.append(f"Hybrid opportunity: {self.config.hybrid_bonus:+d}")

        estimated = record.estimated_value
        if estimated is not None:
            minimum = (
                Decimal(self.config.minimum_value)
                if self.config.minimum_value is not None
                else None
            )
            maximum = (
                Decimal(self.config.maximum_value)
                if self.config.maximum_value is not None
                else None
            )
            in_range = True
            if minimum is not None and estimated < minimum:
                in_range = False
            if maximum is not None and estimated > maximum:
                in_range = False
            if in_range and (minimum is not None or maximum is not None):
                total += self.config.value_in_range_bonus
                reasons.append(
                    f"Value within configured range: {self.config.value_in_range_bonus:+d}"
                )

        deadline = self.deadlines.evaluate(record.deadline_at)
        if deadline.status.value == "EXPIRED":
            total += self.config.expired_penalty
            reasons.append(f"Deadline expired: {self.config.expired_penalty:+d}")
        elif deadline.days_remaining is None:
            total += self.config.missing_deadline_penalty
            reasons.append(f"Missing deadline: {self.config.missing_deadline_penalty:+d}")
        elif (
            self.config.deadline_min_days
            <= deadline.days_remaining
            <= self.config.deadline_max_days
        ):
            total += self.config.deadline_in_range_bonus
            reasons.append(
                f"Deadline within configured range: {self.config.deadline_in_range_bonus:+d}"
            )

        clamped = max(0, min(100, total))
        if not reasons:
            reasons.append("No scoring signals matched; baseline score applied")

        payload = record.model_dump()
        payload.update(
            {
                "score": clamped,
                "score_rating": rating_for_score(clamped),
                "score_reasons": reasons,
                "deadline_status": deadline.status,
                "days_remaining": deadline.days_remaining,
            }
        )
        return ScoredOpportunity.model_validate(payload)
