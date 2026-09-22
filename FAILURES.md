# Failure modes, fixes, and results

Honest engineering notes for this project. Nothing here is invented for polish.

## What can go wrong

- **One bad source aborting the whole run.** Impact: missed opportunities. Mitigation: per-source failure isolation; other connectors continue (`ARCHITECTURE.md` failure boundaries).
- **Invalid records silently dropped.** Impact: invisible data loss. Mitigation: validation errors go to `ingestion_errors`; provenance keeps raw payloads.
- **Aggressive auto-merge of near-duplicates.** Impact: wrong canonical row. Mitigation: explicit `AMBIGUOUS` state (ADR on ambiguous duplicates); not auto-merged.
- **Vercel read-only filesystem / local SQLite paths.** Impact: serverless crash on cold start. Mitigation: force `/tmp` SQLite when `DATABASE_URL` points at local paths; bundled seed DB for instant boot (commits on `main`).

## What went wrong

Evidence from commit history (real deploy fixes, not invented outages):

1. Vercel serverless crashed on cold start when SQLite paths were not writable.
2. Project env copied `sqlite+aiosqlite:///./data/...` which is read-only on Vercel.
3. CI formatting failed; Vercel entrypoint was wrong relative to docs.
4. Pipeline-on-boot was too heavy for cold starts.

## How it was resolved

1. `/tmp` SQLite with resilient bootstrap, slim requirements, explicit `index.py` entrypoint (`c8aacee`).
2. Ignore local-path SQLite URLs unless PostgreSQL is configured (`97f2c0d`).
3. Ruff format + `tool.vercel.entrypoint = index:app` (`ecebb17`).
4. Bundled seed database copied into `/tmp` instead of running the full pipeline on boot (`dcf7a73`).

## Results

From `BUILD_REPORT.md` (26 August 2026):

- **33 passed** in ~57-66s; coverage run documented in the same report.
- Demo run: `sources_successful=4`, `sources_failed=0`; invalid fixtures landed in `ingestion_errors`.
- Idempotent second demo run does not double counts.
- Live demo URL in repo metadata (Vercel). Successful local demo: `uv run opportunity-engine demo`, API, dashboard.
