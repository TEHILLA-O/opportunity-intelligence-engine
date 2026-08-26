# Contributing

This repository is a self-directed engineering case study. Small, reviewable changes are welcome.

## Setup

```bash
cp .env.example .env
uv sync --group dev
uv run alembic upgrade head
uv run pytest
```

## Conventions

- Python 3.12+, type hints on public functions
- Ruff for lint and format
- mypy on `app/`
- Do not scrape sources that disallow automation
- Do not commit secrets, database files or generated Excel exports
- Keep the core pipeline deterministic and independent of any LLM

## Pull requests

Use the PR template. Include test updates for behavioural changes.
