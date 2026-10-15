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
- `apps/api/src/registry`: REST API endpoints to register, list, get, and version agents
  - Pydantic response models (`schemas.py`): `AgentResponse`, `AgentDetailResponse`, `AgentListResponse`, `AgentVersionSummaryResponse`, `AgentVersionDetailResponse`, `ValidationErrorDetail`
  - Service layer (`service.py`): UUID/slug resolution, filtered pagination, spec validation via `packages/spec`, version immutability enforcement
  - Endpoints (`router.py`): `POST /api/v1/agents`, `GET /api/v1/agents`, `GET /api/v1/agents/{id_or_name}`, `GET /api/v1/agents/{id_or_name}/versions`, `GET /api/v1/agents/{id_or_name}/versions/{version}`, `POST /api/v1/agents/{id_or_name}/versions`
  - Coverage & concurrency: Configured `greenlet` and `thread` concurrency in `pyproject.toml`
  - 13 integration tests (`test_router.py`) with 100% test coverage on `registry/` modules
- `docs/adr/0004-registry-api-design.md` — ADR documenting registry API routes, immutability rules, and service layer architecture
- `apps/api/src/runtime`: Runtime Protocol, LangGraph single-prompt adapter, and run execution endpoints
  - `Runtime` protocol & dataclasses (`interface.py`): `@runtime_checkable Protocol`, `RunContext`, `RunResult`
  - LangGraph adapter (`adapter.py`): `StateGraph` compiled single-prompt workflow invoking LiteLLM, calculating tokens and cost, with JSON parsing and exception handling
  - Mock runtime (`mock.py`): Deterministic, offline execution engine supporting failure injection and approval-waiting states
  - Schemas (`schemas.py`): `RunCreateRequest`, `RunResponse`, `RunListResponse`
  - Service layer (`service.py`): `trigger_agent_run()`, `get_run()`, `list_runs_for_agent()` with lifecycle status updates (`running` -> `completed` / `failed`)
  - Endpoints (`router.py`): `POST /api/v1/agents/{id_or_name}/runs`, `GET /api/v1/agents/{id_or_name}/runs`, `GET /api/v1/runs/{id}`
  - 15 unit and integration tests with 97% overall coverage on `runtime/`
- `docs/adr/0005-runtime-interface-and-langgraph-adapter.md` — ADR documenting runtime decoupling, LangGraph encapsulation, LiteLLM usage, and mock runtime strategy
- New dependency: `langgraph>=0.2.0` (MIT, added to `varistha-api`)
- `apps/api/src/plugins` and `plugins/web-fetch`: MCP Plugin Host and web-fetch plugin with SSRF protection
  - Plugin manifest validation (`manifest.py`): Pydantic model enforcing `name`, `version`, `entrypoint`, `scopes`, `risk` level, and `untrusted_output` flag
  - Plugin host (`host.py`): Plugin discovery across filesystem directories, tool schema inspection, and permission gating outside the model (`is_plugin_enabled`)
  - Web fetch plugin (`plugins/web-fetch`): Async HTTP fetcher (`fetcher.py`) with HTML text extraction, `<title>` extraction, script/style sanitization, and redirect safety
  - SSRF protection (`ssrf.py`): Strict IPv4/IPv6 validation blocking loopback (`127.0.0.0/8`, `::1`), RFC 1918 private ranges, cloud metadata endpoints (`169.254.169.254`), CGNAT (`100.64.0.0/10`), non-HTTP schemes, and credentials in URLs
  - Untrusted output tagging: Web responses explicitly flagged with `untrusted: True`
  - 37 unit tests across host, SSRF, and fetcher modules with 98% overall test coverage
- `docs/adr/0006-mcp-plugin-host-and-ssrf-protection.md` — ADR documenting plugin architecture, security boundaries, and SSRF defense-in-depth

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
