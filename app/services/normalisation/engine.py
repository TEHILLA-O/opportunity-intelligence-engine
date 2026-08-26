"""Deterministic record normalisation."""

from __future__ import annotations

from pydantic import ValidationError

from app.core.exceptions import RecordValidationError
from app.schemas.opportunity import NormalisedOpportunity
from app.schemas.raw import RawOpportunityIn
from app.services.deduplication.fingerprint import content_hash_from_raw, identity_fingerprint
from app.services.normalisation.currency import parse_money
from app.services.normalisation.dates import parse_datetime
from app.services.normalisation.locations import normalise_location
from app.services.normalisation.taxonomy import (
    parse_contract_type,
    parse_procurement_type,
    parse_remote_status,
    parse_status,
)
from app.services.normalisation.text import (
    canonical_url,
    collapse_whitespace,
    extract_emails,
    extract_keywords,
    normalise_organisation,
    normalise_title,
    strip_html,
    summarise,
)


class NormalisationEngine:
    def normalise(self, raw: RawOpportunityIn) -> NormalisedOpportunity:
        title = collapse_whitespace(raw.raw_title)
        if not title:
            raise RecordValidationError(
                "Opportunity is missing a title",
                details={"external_id": raw.external_id, "source": raw.source_name},
            )
        description = strip_html(raw.raw_description)
        organisation = collapse_whitespace(raw.raw_organisation)
        location, country, _ = normalise_location(raw.raw_location)
        minimum_value, maximum_value, estimated_value, currency = parse_money(raw.raw_value)
        deadline_at = parse_datetime(raw.raw_deadline)
        published_at = parse_datetime(str(raw.raw_metadata.get("published_at") or "")) or None
        source_url = collapse_whitespace(raw.source_url)
        if source_url:
            from app.core.security import is_public_http_url

            if not is_public_http_url(source_url) and not source_url.startswith("file:"):
                # Allow relative/demo URLs that already look like http(s); reject junk.
                if not source_url.startswith(("http://", "https://")):
                    raise RecordValidationError(
                        "Invalid source URL",
                        details={"source_url": source_url, "source": raw.source_name},
                    )
        emails = extract_emails(
            " ".join(
                part for part in (raw.raw_contact_email, description, raw.raw_description) if part
            )
        )
        contact_email = (
            raw.raw_contact_email or (emails[0] if emails else None) or ""
        ).strip() or None
        try:
            return NormalisedOpportunity(
                source_name=raw.source_name,
                external_id=collapse_whitespace(raw.external_id),
                title=title,
                organisation=organisation,
                description=description,
                summary=summarise(description or title),
                category=collapse_whitespace(raw.raw_category)
                or collapse_whitespace(str(raw.raw_metadata.get("category") or "")),
                location=location,
                country=country,
                remote_status=parse_remote_status(raw.raw_location, description),
                procurement_type=parse_procurement_type(
                    title, str(raw.raw_metadata), raw.raw_category
                ),
                contract_type=parse_contract_type(title, str(raw.raw_metadata), raw.raw_category),
                currency=currency,
                minimum_value=minimum_value,
                maximum_value=maximum_value,
                estimated_value=estimated_value,
                published_at=published_at,
                deadline_at=deadline_at,
                source_url=source_url,
                canonical_url=canonical_url(source_url),
                contact_name=collapse_whitespace(raw.raw_contact_name),
                contact_email=contact_email,
                requirements=strip_html(raw.raw_requirements),
                skills=raw.raw_skills or list(raw.raw_metadata.get("skills") or []),
                keywords=extract_keywords(" ".join(filter(None, [title, description]))),
                status=parse_status(str(raw.raw_metadata.get("status") or "")),
                content_hash=raw.content_hash
                or content_hash_from_raw(
                    title=raw.raw_title,
                    description=raw.raw_description,
                    organisation=raw.raw_organisation,
                    location=raw.raw_location,
                    value=raw.raw_value,
                    deadline=raw.raw_deadline,
                    url=raw.source_url,
                    extra=raw.raw_metadata,
                ),
                fingerprint=identity_fingerprint(
                    title=title, organisation=organisation, canonical=source_url
                ),
                normalised_title=normalise_title(title),
                normalised_organisation=normalise_organisation(organisation),
                raw_payload=raw.model_dump(mode="json"),
            )
        except ValidationError as exc:
            raise RecordValidationError(
                "Normalised record failed schema validation",
                details={"errors": exc.errors(), "source": raw.source_name},
            ) from exc
