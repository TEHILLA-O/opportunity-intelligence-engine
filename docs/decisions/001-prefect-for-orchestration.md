# ADR 001: Prefect for optional orchestration

## Context

The pipeline must run locally without infrastructure, in tests, from the CLI, and on a schedule.

## Decision

Implement the pipeline as an in-process async service (`OpportunityPipeline`). Wrap that service with Prefect 3 flows for environments that already run Prefect. The CLI demo does not require a Prefect server.

## Alternatives Considered

- Prefect-only execution
- Celery / Redis
- Cron calling a script with no workflow metadata

## Consequences

Local demos stay simple. Scheduling is available without making Prefect a runtime dependency of tests or SQLite demos.
