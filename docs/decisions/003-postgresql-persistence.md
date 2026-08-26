# ADR 003: PostgreSQL persistence with SQLite for local demo

## Context

Production needs concurrent writers, Numeric money columns and operational backups. Developers need a zero-config demo.

## Decision

SQLAlchemy 2 with async engines. PostgreSQL (`asyncpg`) is the primary production database. SQLite (`aiosqlite`) is the default local/demo database. Alembic migrations use portable types.

## Alternatives Considered

- SQLite only
- MongoDB for raw payloads
- Dual writes to a warehouse

## Consequences

Money is stored as `Numeric`, not floats. Some PostgreSQL-only features (partial unique indexes) are deferred so SQLite demos keep working.
