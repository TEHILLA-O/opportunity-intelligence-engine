# ADR 006: Multi-signal deduplication with an AMBIGUOUS state

## Context

The same tender appears under different IDs and slightly different titles. Auto-merging uncertain matches corrupts history.

## Decision

Confirm duplicates on exact source ID, canonical URL or content hash. Use fuzzy title plus organisation and deadline as supporting signals. Borderline scores create `duplicate_candidates` with status `AMBIGUOUS` and do not merge.

## Alternatives Considered

- Hash-only matching
- Always merge above a fuzzy threshold
- External entity-resolution SaaS

## Consequences

Uncertain matches remain visible for review. Idempotent re-runs do not explode row counts for confirmed identities.
