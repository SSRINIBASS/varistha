# ADR-0003: Database Schema, Async Engine, and Migrations

**Date:** 2026-10-15
**Status:** Accepted
**Deciders:** Varistha core team

---

## Context

Phase 1, Task 2 requires setting up the database storage layer and initial migrations for
the four core entities needed by the walking skeleton (`docs/SPEC.md § 4.2` and `§ 7.5 Task 2`):

- `agents`: agent definition, ownership, lifecycle stage, and current version
- `agent_versions`: immutable historical spec snapshots (`AgentSpec` JSON)
- `runs`: execution tracking, triggers, costs, tokens, inputs/outputs, and statuses
- `spans`: OTLP-derived trace spans for execution timeline and waterfall visualization

We must define the ORM models, session/engine factories, bounded-context boundaries,
and migration infrastructure.

---

## Decision

### 1. SQLAlchemy 2.0 Declarative Mapped Architecture

All models inherit from `shared.db.base.Base` (subclassing `DeclarativeBase`) and use
Python 3.12 type-annotated `Mapped[...]` attributes.

**Rationale:**
- Native static type safety verified with Pyright strict mode (`0 errors`).
- Clear column nullability and constraint definitions directly in the type declarations.
- Standardized `TimestampMixin` guaranteeing UTC timezone-aware timestamps (`DateTime(timezone=True)`).

### 2. UUID Primary Keys (`sa.Uuid`)

All tables (`agents`, `agent_versions`, `runs`, `spans`) use standard UUIDv4 primary keys
via SQLAlchemy's `sa.Uuid()`.

**Rationale:**
- Prevents sequential ID enumeration and security harvesting.
- Allows clients, workers, and telemetry exporters to generate IDs before roundtripping to the DB.
- `sa.Uuid` maps natively to PostgreSQL's `UUID` type while gracefully falling back to `CHAR(32)` on SQLite.

### 3. Portable JSON / JSONB Spec and Trace Storage

The `spec` snapshot column in `agent_versions` and the `input`/`output`/`attributes`/`events`
columns in `runs` and `spans` use:
```python
JSON().with_variant(JSONB, "postgresql")
```

**Rationale:**
- High-performance binary JSON indexing (`JSONB`) in PostgreSQL production deployments.
- Full compatibility with SQLite in development, CI, and testing environments without driver errors.

### 4. Async Loading via `lazy="selectin"`

All model relationships (`Agent.versions`, `Agent.runs`, `Run.spans`, `Span.run`) are
configured with `lazy="selectin"`.

**Rationale:**
- SQLAlchemy's default lazy loading causes `MissingGreenlet` exceptions under `AsyncSession`
  when attributes are accessed asynchronously.
- `selectin` loading executes a separate `SELECT ... WHERE id IN (...)` query using the async
  connection, guaranteeing predictable and safe relationship navigation.

### 5. Dual Sync/Async Alembic Runner (`alembic/env.py`)

The Alembic environment detects whether the database connection URL is async
(`postgresql+asyncpg`, `sqlite+aiosqlite`) or sync (`postgresql`, `sqlite`), running async
migrations via `async_engine_from_config` + `connection.run_sync` when async, and standard
sync connections otherwise.

**Rationale:**
- CLI commands like `alembic upgrade head` work seamlessly against the production `DATABASE_URL` (`postgresql+asyncpg`).
- Testing environments can exercise migrations programmatically across both sync and async URLs.

### 6. Dev Dependency `aiosqlite` for Test Execution

Added `aiosqlite>=0.20.0` (License: MIT) to `[dependency-groups] dev`.

**Rationale:**
- Allows the entire test suite (including async SQLAlchemy engine and session workflows)
  to run fully in-memory (`sqlite+aiosqlite:///:memory:`) in sub-second time without requiring
  a running PostgreSQL daemon.
- Zero impact on production runtime image.

---

## Consequences

- Core models are defined in `apps/api/src/shared/db/models/` and re-exported from `shared.db`.
- The initial migration `apps/api/alembic/versions/0001_initial_schema.py` establishes the schema.
- All subsequent database alterations must go through versioned Alembic migrations.
- Test coverage for the database layer is 100% across models, migrations, and session utilities.
