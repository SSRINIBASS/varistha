# Milestone Checkpoint: Phase 1, Task 2 — Database Schema & Migrations

- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 2 — Database schema and migrations for agents, agent_versions, runs, and spans
- **Status**: PASSED
- **Timestamp**: 2026-10-15T12:58:45+05:30
- **Git Commit**: `c516249`
- **Reference Spec**: `docs/SPEC.md § 4.2 & § 7.5 Task 2`

---

## 1. Implemented Capabilities

1. **SQLAlchemy 2.0 Async Models (`apps/api/src/shared/db/models/`)**:
   - `Agent`: UUID primary key, unique indexed slug name, owner email, stage (default "draft"), current_version, UTC timestamps.
   - `AgentVersion`: UUID primary key, agent_id foreign key (CASCADE), semver version string, immutable spec snapshot (JSON with PostgreSQL JSONB variant), unique constraint on `(agent_id, version)`.
   - `Run`: UUID primary key, agent_id foreign key (CASCADE), agent_version_id foreign key (SET NULL), status (pending/running/completed/failed/cancelled/waiting_approval), trigger_type (manual/schedule/webhook), input/output JSON, cost in USD, total tokens, timestamps.
   - `Span`: UUID primary key, run_id foreign key (CASCADE), trace_id, span_id, parent_span_id, name, kind, status, attributes, events, timestamps.
   - All relationships use `lazy="selectin"` for safe async navigation without `MissingGreenlet` exceptions.
2. **Session & Engine Management (`apps/api/src/shared/db/session.py`)**:
   - `get_async_engine()` and `get_session_factory()`.
   - FastAPI dependency `get_db_session()` with automatic commit and error rollback.
   - SQLite PRAGMA hook ensuring foreign key cascade checks execute identically in tests.
3. **Application Configuration (`apps/api/src/shared/config.py`)**:
   - `pydantic-settings` BaseSettings class for `DATABASE_URL`, `ENVIRONMENT`, `LOG_LEVEL`, `SECRET_KEY`.
4. **Alembic Migration Suite (`apps/api/alembic/`)**:
   - `alembic.ini` and `env.py` supporting dual async (`postgresql+asyncpg`, `sqlite+aiosqlite`) and sync database connections.
   - Initial migration `0001_initial_schema.py` creating all four tables, constraints, and indexes.

---

## 2. Test & Quality Metrics

- **Unit & Integration Tests Added**: 14 (7 model tests, 2 migration tests, 5 session tests)
- **Cumulative Tests**: 41 passing
- **Test Coverage**: 96.0% overall on `shared/` and `spec/` (exceeds ≥ 80% gate)
- **Linter Status**: `ruff check` clean (0 errors)
- **Type Checker Status**: `pyright` strict clean (0 errors)
- **Architecture Boundaries**: `OK: All architecture boundaries respected.`
- **Architectural Decision Record**: `docs/adr/0003-database-schema-and-migrations.md`
- **Dependencies Added**: `aiosqlite>=0.20.0` (MIT license, dev group)
