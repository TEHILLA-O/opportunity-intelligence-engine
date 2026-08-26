# ADR 002: Source adapter pattern

## Context

Opportunity data arrives as JSON, RSS, HTML and synthetic demo files. Callers should not branch on source type.

## Decision

Define `OpportunitySource` with `fetch()` and `healthcheck()`. Register connectors from `config/sources.yaml`. Isolate failures per source.

## Alternatives Considered

- One scraper class with type switches
- Airbyte-style ELT with an external orchestrator

## Consequences

New sources can be added without changing the pipeline. Disabled remote examples stay in config as documentation, not live traffic.
