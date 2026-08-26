# ADR 005: Preserve raw source data

## Context

Normalisation loses information. Duplicate disputes and change detection need provenance.

## Decision

Write `raw_opportunities` before creating or updating `opportunities`. Store source, URL, external ID, retrieval time, raw fields, content hash and HTTP metadata.

## Alternatives Considered

- Normalise in memory and persist only the clean model
- Store raw blobs in object storage only

## Consequences

Storage grows faster. Traceability from a scored row back to the collected payload is a first-class feature.
