# ADR 004: Deterministic scoring

## Context

Suitability ranking must be explainable in interviews, audits and Excel reports. An LLM score cannot be the system of record.

## Decision

Score 0–100 from `config/scoring.yaml`. Persist `score_reasons`. Optional enrichment adapters may suggest summaries later; they cannot replace this engine.

## Alternatives Considered

- Machine-learned ranker
- LLM classification
- Manual spreadsheet weighting

## Consequences

Changing weights does not require a code change. Tests can assert reasons, not just a magic number.
