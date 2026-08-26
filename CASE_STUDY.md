# Opportunity Intelligence Automation Engine

## Executive Summary

Opportunity Engine is a self-directed Python automation case study. It ingests commercial opportunity records from multiple connectors, keeps raw provenance, normalises messy fields, deduplicates, scores with explanations, and publishes results through reports, an API and a dashboard.

It is not a commissioned product and does not claim customer savings.

## Business Problem

Manual opportunity monitoring fails because sources disagree on schema, the same notice is republished, deadlines move, and spreadsheets drift out of date.

## Engineering Challenge

Build a pipeline that is idempotent, auditable and resilient when one source fails — and that can be demonstrated offline with bundled fictional data.

## Objectives

- End-to-end automation without an LLM
- Traceability from scored row to raw payload
- Explainable ranking
- Tests that lock behaviour, not trivia

## System Architecture

Modular FastAPI service with a repository layer and source adapters. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Data Pipeline

Collection, raw store, validation, normalisation, fingerprints, deduplication, change detection, scoring, persistence, reporting, notification, metrics.

## Multi Source Collection Strategy

Mock (required for demo), JSON, RSS, HTML, optional Playwright. Concurrent fetch with isolation. Responsible HTTP defaults.

## Normalisation

Whitespace, HTML text, UK/ISO dates, currency and ranges to `Decimal`, UK locations, contract taxonomy, canonical URLs, email extraction.

## Deduplication Strategy

Exact source ID → canonical URL → content hash → normalised title+organisation → fuzzy title with organisation/deadline support. Uncertain pairs are `AMBIGUOUS`.

## Scoring System

YAML weights, score 0–100, rating bands, persisted reason strings.

## Idempotency

Re-running the demo must not double opportunity rows. Confirmed identities update `last_seen_at` or history; they do not insert clones.

## Failure Recovery

Timeouts, bounded retries, exponential backoff, ingestion error table, source health degradation after consecutive failures.

## Observability

Structured logs, per-stage run steps, stored metrics JSON.

## Database Design

SQLAlchemy 2, UUID keys, Numeric money, Alembic, SQLite or PostgreSQL.

## API Design

Versioned `/api/v1` routes, pagination, filtering, consistent `{ "error": { "code", "message", "details" } }` bodies, documented OpenAPI.

## Reporting

Multi-sheet Excel with filters, freeze panes, currency formats and score colour scales, plus CSV/JSON.

## Testing Strategy

Unit tests for parsers and scoring; integration tests for pipeline idempotency and API; HTTP mocked with respx; no live website dependency in CI.

## Security Considerations

See [SECURITY.md](SECURITY.md). No secrets in the repo. Scraping restrictions respected.

## Performance Considerations

Demo volume is laptop-friendly (roughly 200 collected records). Benchmark script: `uv run python scripts/benchmark_pipeline.py --records 200`. Measured numbers belong in [BUILD_REPORT.md](BUILD_REPORT.md) after a local run.

## Key Engineering Decisions

Prefect as wrapper, source adapters, raw preservation, deterministic scoring, ambiguous duplicates. ADRs live in `docs/decisions/`.

## Challenges and Solutions

SQLite vs PostgreSQL portability: use generic SQLAlchemy types. Duplicate explosions: identity lookup before insert. Malformed money/dates: parse defensively and keep the rest of the batch.

## Results

Engineering measurements from this repository (26 August 2026). Details: [BUILD_REPORT.md](BUILD_REPORT.md).

- Demo collected **249** records from four bundled sources in **6.71s**
- Stored **26** unique opportunities after deduplication
- Identified **180** confirmed duplicates and **41** ambiguous pairs
- Rejected **2** invalid records into `ingestion_errors` (missing title; invalid URL)
- Second demo run: **0** new rows, **0** updates — counts did not double
- `--apply-updates` run detected **2** field-level changes
- Excel workbooks generated after successful runs
- **33** pytest tests passed; coverage **83.87%** of application code
- Ruff: all checks passed; mypy: 89 files, no issues
- Fresh-DB benchmark: **199** demo records in **5.58s** (**35.4** records/s)

These figures are local engineering measurements. They are not business ROI.

## What I Would Improve for Production

Allow-listed live sources, PostgreSQL partial unique indexes, a review queue for ambiguous duplicates, object storage for raw HTML, authentication in front of the API.

## Skills Demonstrated

Python automation, ETL, HTTP clients, HTML/RSS/JSON parsing, SQLAlchemy, FastAPI, testing, Docker, structured logging, explainable scoring, responsible collection.
