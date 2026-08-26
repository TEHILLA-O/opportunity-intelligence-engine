FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
COPY app ./app
COPY config ./config
COPY migrations ./migrations
COPY alembic.ini ./
COPY data ./data

RUN uv sync --frozen --no-dev --no-install-project --extra orchestration || uv sync --no-dev --extra orchestration
RUN uv pip install --system -e .

EXPOSE 8000

HEALTHCHECK --interval=20s --timeout=5s --retries=5 CMD curl -f http://localhost:8000/health || exit 1

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
