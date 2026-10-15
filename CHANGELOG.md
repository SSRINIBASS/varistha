# Changelog

All notable changes to Varistha will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 2 — Registry and Lifecycle

#### Added
- `packages/spec/src/diff.py`: Pure deterministic Spec Diffing Engine for comparing AgentSpec versions
  - Detects field-level deltas across metadata, role, models, instructions, autonomy, plugins, guardrails, budgets, triggers, and evals
  - Classifies changes as breaking vs non-breaking with explicit explanatory reasons (autonomy escalation, guardrail removal, primary model changes, budget reductions, plugin removal)
  - 100% test coverage with 21 unit tests in `packages/spec/tests/test_diff.py`
- `apps/api/src/registry/diff_service.py` & `router.py`: REST endpoints for spec version diffing
  - `GET /api/v1/agents/{id_or_name}/versions/{v1}/diff/{v2}`: Compares two published immutable versions
  - `POST /api/v1/agents/{id_or_name}/diff`: Previews candidate spec diff and breaking change warnings against current active or target base version
- `packages/cli`: `varistha diff` CLI command
  - Compares published versions (`varistha diff <agent> <v1> <v2>`) or local files (`varistha diff -f agent.yaml`)
  - Supports `--strict` gate to exit with non-zero code on breaking changes
  - Rich terminal formatting with color badges and breaking change alerts
- `docs/adr/0011-spec-diffing-engine-and-breaking-changes.md`: ADR documenting spec diffing architecture and breaking change taxonomy
- `apps/api/src/shared/db/models/stage_transition.py`: `StageTransition` model for immutable audit trail of agent lifecycle changes
- `apps/api/alembic/versions/0002_stage_transitions.py`: Alembic migration creating `stage_transitions` table with cascade delete and foreign key indexing
- `apps/api/src/registry/gates.py`: Pure domain gate evaluation engine for lifecycle transitions (`Draft` → `Prototype` → `Staging` → `Production` → `Deprecated` → `Retired`)
  - Evaluates spec validity, successful execution runs, owner presence, guardrail attachments, eval suite thresholds, budget spend caps, and kill-switch confirmations
  - Validates rollbacks and demotions with mandatory explanatory reason logging
- `apps/api/src/registry/router.py`: REST endpoints for lifecycle governance
  - `POST /api/v1/agents/{id_or_name}/promote`: Evaluate gates, advance agent stage, record immutable audit entry
  - `GET /api/v1/agents/{id_or_name}/history`: Query chronological stage transition audit history
  - `GET /api/v1/agents/{id_or_name}/gates/{target_stage}`: Dry-run preview endpoint for live UI checklists
- `docs/adr/0010-stage-promotion-gates-and-audit-log.md`: Architecture decision record for stage transitions and gates
- Full suite passing: 214 tests across monorepo with 96% overall test coverage


### Phase 1 — Walking Skeleton (Week 2-3)

#### Added
- `apps/ui`: Minimal Web UI dashboard (Next.js 16 App Router, TypeScript strict mode, Tailwind CSS v4, Lucide icons)
  - Agents Registry View (`/agents` and `/`): Dense table of registered AI employees, search and stage filters, stage badges (`Draft`, `Prototype`, `Staging`, `Production`, `Deprecated`, `Retired`), autonomy tags (`L0`-`L3`), and run triggers
  - Execution Runs View (`/runs`): Historical and active runs monitor with status badges, token usage, cost attribution, and trace view links
  - Trace Waterfall View (`/runs/[id]`): High-fidelity custom Gantt timeline displaying root `agent.run` and child `llm.call` spans with offset calculations, duration bars, and interactive span attribute inspection
  - Design system compliance: Non-blocking loading skeletons, empty state guides, error alerts with retry handlers, and zero hardcoded colors
  - Interactive Run Trigger Modal (`TriggerRunModal`): Form for testing and executing agent runs with JSON payload validation directly from the browser
  - API Integration: Added `CORSMiddleware` in `apps/api/src/main.py` and global `GET /api/v1/runs` endpoint in `runtime/router.py`
  - 17 Vitest unit and component tests passing cleanly
- `docs/adr/0009-minimal-ui-architecture-and-waterfall.md` — ADR documenting UI architecture, custom trace waterfall, and design system
- `packages/cli`: Varistha CLI developer workflow commands (`init`, `apply`, `run`)
  - Scaffolding (`varistha init [NAME]`): Interactive or flag-driven creation of canonical `agent.yaml` specifications compliant with `varistha-spec`
  - Declarative sync (`varistha apply -f <path>`): Offline local spec validation followed by idempotent API registration (`POST /api/v1/agents` or `POST /api/v1/agents/{id}/versions`)
  - Execution run (`varistha run <id-or-name>`): Trigger runs via API with polling watch mode spinner, USD cost attribution, token breakdowns, trace ID display, and machine-readable `--json` output
  - Rich terminal formatting with cross-platform CP1252/Windows console resilience
  - Decoupled HTTP client (`VaristhaClient`) communicating strictly via REST endpoints with zero internal API code imports
  - 37 unit and integration tests; 94% test coverage on `packages/cli`
- `docs/adr/0008-cli-architecture-and-workflow.md` — ADR documenting CLI architecture, client boundaries, offline validation, and watch mode polling
- `apps/api/src/observability` and `apps/api/src/shared/telemetry`: OpenTelemetry instrumentation, OTLP/HTTP receiver, and span persistence
  - OpenTelemetry semantic conventions (`conventions.py`): `varistha.*` attributes and GenAI conventions (`gen_ai.*`)
  - PII and secret redaction (`redaction.py`): Automatic sanitization of bearer tokens, API keys, passwords, and emails
  - OTLP/HTTP receiver endpoints (`router.py`): `POST /v1/traces` and `POST /api/v1/traces` supporting standard OTLP JSON export with Protobuf AnyValue decoding
  - Span persistence & queries: Storage in `spans` table, queried via `GET /api/v1/runs/{id}/spans` and `GET /api/v1/traces/{trace_id}`
  - Decoupled runtime tracing: In-process span recorder capturing `agent.run` root spans and `llm.call` child spans without cross-context import violations
  - 20 unit and integration tests across parser, telemetry, and router with 93% test coverage
- `docs/adr/0007-opentelemetry-instrumentation-and-otlp-receiver.md` — ADR documenting OpenTelemetry architecture, OTLP receiver, and span persistence
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
