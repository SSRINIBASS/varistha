# Changelog

All notable changes to Varistha will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 1 — Walking Skeleton (Week 2-3)

#### Added
- `packages/spec`: Agent Spec Pydantic v2 models, YAML/dict validator, JSON Schema generator
  - Models: `AgentSpec`, `AgentMetadata`, `AgentSpecBody`, `ModelConfig`, `PluginRef`,
    `GuardrailsConfig`, `BudgetConfig`, `TriggerConfig`, `EvalConfig`
  - `validate_spec(raw: dict) -> AgentSpec` and `validate_spec_yaml(yaml: str) -> AgentSpec`
  - `SpecValidationError` with human-readable, location-prefixed error messages
  - `packages/spec/src/schema.json` — committed JSON Schema for editor tooling
  - `packages/spec/tests/fixtures/lead-researcher.yaml` — reference fixture from SPEC.md § 3.4
  - 25 unit tests; 84.5% coverage
- `docs/adr/0002-agent-spec-schema.md` — Pydantic v2 choice, `extra=forbid` policy,
  instructions-as-string rationale, autonomy Literal enum rationale
- New dependency: `email-validator>=2.1` (MIT) for `EmailStr` owner field validation
- `apps/api/src/shared/db`: SQLAlchemy 2.0 async database layer & Alembic migrations
  - ORM models: `Agent`, `AgentVersion`, `Run`, and `Span` with UUID primary keys, JSONB/JSON spec snapshots, cascading deletes, and `lazy="selectin"` async relationships
  - Database engine and session factory (`apps/api/src/shared/db/session.py`) with `get_db_session()` dependency generator
  - Application settings (`apps/api/src/shared/config.py`) via `pydantic-settings`
  - Alembic configuration (`apps/api/alembic.ini`, `apps/api/alembic/env.py`) supporting both async (`postgresql+asyncpg`, `sqlite+aiosqlite`) and sync database connections
  - Baseline migration `0001_initial_schema.py` creating `agents`, `agent_versions`, `runs`, and `spans` tables with indexes and constraints
  - 14 new unit and integration tests (7 model tests, 2 migration tests, 5 session tests) with 96% coverage
- `docs/adr/0003-database-schema-and-migrations.md` — ADR documenting database architecture, UUIDs, JSONB variants, selectin loading, and migration strategy
- New dev dependency: `aiosqlite>=0.20.0` (MIT) for fast in-memory async database testing

### Phase 0 — Foundations (Week 1)


#### Added
- Monorepo structure: `apps/api`, `apps/worker`, `apps/ui`, `packages/cli`, `packages/spec`, `packages/sdk`, `plugins/`, `role-packs/`, `docs/`, `deploy/`
- Python workspace with `uv`: FastAPI placeholder with `/health` and `/` endpoints
- `pyproject.toml` with ruff (full lint suite), pyright strict, pytest, bandit, pip-audit
- Two passing smoke tests for health and root endpoints
- `AGENTS.md` and `GEMINI.md` — agent instructions for AI-assisted development
- `LICENSE` (Apache-2.0), `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- `CHANGELOG.md` (this file)
- `docs/SPEC.md` — product specification
- `docs/adr/0001-monorepo-and-stack.md` — ADR for monorepo and stack decisions
- `.github/workflows/ci.yml` — CI pipeline (lint, type-check, test)
- `.github/workflows/code-review.yml` — automated code review pipeline
- `deploy/docker-compose.yml` — Postgres, API and UI placeholders
- `deploy/.env.example` — documented environment variables
- `scripts/check_boundaries.py` — architecture boundary enforcement

[Unreleased]: https://github.com/your-org/varistha/compare/HEAD...HEAD
