# Build Report

Measured on 26 August 2026, Windows 10, Python 3.12.11, `uv 0.12.6`.

## Build Status

**Complete and demonstrable.** The pipeline, tests, lint, typecheck, demo, Excel export, API and dashboard were executed in this repository. This is a self-directed engineering case study, not a client deployment.

## Implemented Features

- Multi-source collection: mock, JSON, RSS, HTML, optional Playwright
- Responsible HTTP client (timeouts, retries, rate limits, User-Agent, robots.txt)
- Raw provenance layer plus normalised opportunities
- Validation with `ingestion_errors` (no silent drops)
- Deterministic normalisation (currency, UK/ISO dates, locations, taxonomy)
- Multi-signal deduplication with `AMBIGUOUS` (not auto-merged)
- Change detection and `opportunity_history`
- Explainable scoring 0–100 from `config/scoring.yaml`
- Deadline urgency classification
- Prefect 3 wrapper (CLI demo does not need a Prefect server)
- Excel / CSV / JSON exports
- Console notifications; optional email and webhook
- FastAPI with pagination, filtering, OpenAPI
- Jinja2 operations dashboard
- Typer CLI including `demo`, `metrics`, `export`, `api`
- SQLite local/demo database; PostgreSQL via Docker Compose
- Alembic migrations, Ruff, mypy, pytest, GitHub Actions

## Repository Structure

```text
app/            API, CLI, dashboard, pipeline, connectors, services
config/         sources.yaml, scoring.yaml
data/demo/      Bundled synthetic feeds (generated, fictional)
migrations/     Alembic
tests/          unit, integration, e2e
scripts/        case-study demo and benchmark
docs/decisions/ ADRs
```

## Test Results

Command: `uv run pytest -q --tb=line`

```text
.................................                                        [100%]
33 passed in 57.32s
```

Earlier full suite (same 33 tests) with coverage:

```text
33 passed in 66.25s
```

Covered behaviours include currency/date parsing, scoring and exclusion keywords, duplicate source ID/URL/title, change detection, HTTP 500/429/retry exhaustion, invalid source config, Excel creation, API pagination/filtering, pipeline idempotency, and database rollback.

## Coverage

Command: `uv run pytest --cov=app --cov-report=term-missing --cov-report=xml`

```text
TOTAL                                        3001    484    84%
Required test coverage of 70.0% reached. Total coverage: 83.87%
```

CLI, Prefect wrappers and Playwright (optional extra) are intentionally lightly covered. CI HTTP tests use `respx`; they do not call live websites.

## Lint Status

Command: `uv run ruff check app tests scripts`

```text
All checks passed!
```

Format: `uv run ruff format --check app tests scripts` — 103 files already formatted.

## Type Check Status

Command: `uv run mypy app`

```text
Success: no issues found in 89 source files
```

## Demo Results

Command: `uv run opportunity-engine demo` (bundled sources only: mock, JSON, RSS, HTML).

**First run**

```text
Run ID     4a5b6257-1068-42bd-a6b3-cd545d255e77
Status     success
Discovered 249
New        26
Updated    0
Duplicates 180
Invalid    2
Duration   6.7136s
Excel      data/exports/opportunities_20260826_082706.xlsx
sources_attempted=4 sources_successful=4 sources_failed=0
ambiguous_duplicates=41
```

Invalid records were missing-title and invalid-URL fixtures, stored in `ingestion_errors`.

**Second run (idempotency)**

```text
Discovered 249
New        0
Updated    0
Duplicates 206
Invalid    2
Duration   3.7615s
Excel      data/exports/opportunities_20260826_082715.xlsx
```

Opportunity count did not increase.

**Change-detection run** (`uv run opportunity-engine demo --apply-updates`)

```text
New        0
Updated    2
Duplicates 204
Invalid    2
Duration   6.3416s
Excel      data/exports/opportunities_20260826_082744.xlsx
```

Console alerts fired for high-priority rows, closing deadlines, and major field changes.

**Metrics after that run** (`uv run opportunity-engine metrics`)

```text
Very High        17
High             3
Medium           2
Low              0
Very Low         4
Healthy sources  4
Stored rows      26
```

249 collected records collapsed to 26 stored opportunities because repeated titles/organisations across the synthetic set were confirmed or marked ambiguous rather than inserted again.

## Performance Results

Fresh SQLite (`scripts/benchmark_pipeline.py --records 200`, demo source only):

```text
discovered         199
new                26
duplicates         138
wall_clock_seconds 5.6158
records_per_second 35.44
pipeline_seconds   5.5812
```

Repeat against an already-populated database:

```text
wall_clock_seconds 2.4135
records_per_second 82.45
pipeline_seconds   2.3929
```

These are laptop measurements, not production SLAs.

## API Endpoints

Verified live on `http://127.0.0.1:8000`:

| Endpoint | Result |
| --- | --- |
| `GET /health` | 200 `{"status":"ok","version":"0.1.0"}` |
| `GET /health/ready` | 200 `{"status":"ok","database":"ok"}` |
| `GET /metrics/summary` | 200 (26 opportunities, 4 healthy sources) |
| `GET /api/v1/opportunities?page_size=5` | 200 `total=26` |
| `GET /api/v1/opportunities/top` | 200 scored rows with reasons available on detail |
| `GET /docs` | 200 |
| `GET /openapi.json` | title `Opportunity Intelligence Automation Engine` |
| `GET /` (dashboard) | 200 + `/static/style.css` 200 |

Also implemented: `/api/v1/opportunities/closing-soon`, `/new`, `/{id}`, `/sources`, `/runs`, `POST /runs`, `POST /exports`.

## Generated Reports

Excel workbooks written under `data/exports/` (gitignored):

- `opportunities_20260826_082706.xlsx` — first demo
- `opportunities_20260826_082715.xlsx` — idempotent re-run
- `opportunities_20260826_082744.xlsx` — change detection

Sheets: Executive Summary, Top Opportunities, All Opportunities, Closing Soon, New Since Last Run, Changed Opportunities, Rejected Low Score, Pipeline Metrics, Source Performance.

## Known Limitations

- Live government/freelance portals are not scraped; demo uses bundled fictional data
- Playwright is optional and unused in CI
- Email/webhook providers stay disabled without credentials
- SQLite returns naive datetimes; the app normalises to UTC on compare/export
- Fuzzy matching is conservative about auto-merge (`AMBIGUOUS` does not insert a second row)
- API has no authentication (local/demo)

## Production Improvements

- PostgreSQL partial unique indexes
- Allow-listed live sources with recorded permission
- Review UI for ambiguous pairs
- Authn/z in front of the API
- Object storage for large raw HTML
- Dedicated worker for scheduled Prefect deployments

## How to Run the Project

```bash
cp .env.example .env
uv sync --group dev
uv run alembic upgrade head
uv run opportunity-engine demo
uv run pytest
uv run opportunity-engine api
```

Windows without `make`: the `uv run …` commands above are the supported interface. With `make`: `make install demo test api`.

Docker: `docker compose up --build` (PostgreSQL + API).

## Recommended Case Study Screenshots

1. Terminal output of `opportunity-engine demo` (first run metrics)
2. Second run showing `New 0`
3. Dashboard home (`http://127.0.0.1:8000/`)
4. Opportunity detail with score reasons
5. FastAPI `/docs`
6. Excel Executive Summary + Top Opportunities sheets
7. `opportunity-engine metrics`
