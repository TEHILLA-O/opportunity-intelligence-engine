PYTHON ?= python
UV ?= uv

.PHONY: install dev demo test coverage lint format typecheck migrate api docker-up docker-down benchmark

install:
	$(UV) sync

dev:
	$(UV) sync --group dev

demo:
	$(UV) run opportunity-engine demo

test:
	$(UV) run pytest

coverage:
	$(UV) run pytest --cov=app --cov-report=term-missing --cov-report=xml

lint:
	$(UV) run ruff check app tests scripts

format:
	$(UV) run ruff format app tests scripts
	$(UV) run ruff check --fix app tests scripts

typecheck:
	$(UV) run mypy app

migrate:
	$(UV) run alembic upgrade head

api:
	$(UV) run opportunity-engine api

docker-up:
	docker compose up --build

docker-down:
	docker compose down

benchmark:
	$(UV) run python scripts/benchmark_pipeline.py --records 200
