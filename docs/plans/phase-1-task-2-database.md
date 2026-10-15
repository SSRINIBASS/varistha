# Plan: Phase 1, Task 2 — Database Schema & Migrations

## Task Restatement & Goal

- **Task**: Database schema and Alembic migrations for `agents`, `agent_versions`, `runs`, and `spans` (SPEC.md § 4.2 & § 7.5 Task 2).
- **Goal**: Establish the persistent storage foundation for Varistha using SQLAlchemy 2.0 (asyncio) and Alembic, supporting UUID primary keys, JSONB/JSON spec payloads, immutable version snapshots, run tracking, and OTLP-compatible span trees.
- **Exit Criteria**:
  - `agents`, `agent_versions`, `runs`, and `spans` tables defined via SQLAlchemy 2.0 declarative models with proper foreign keys, constraints, and indexes.
  - Alembic configuration initialized (`apps/api/alembic/`) with the first migration script `0001_initial_schema.py` applying clean upgrades and downgrades.
  - Async session factory and database engine utilities in `apps/api/src/shared/db/`.
  - Comprehensive unit and migration tests with ≥ 80% coverage.
  - All automated checks pass (`ruff`, `pyright`, `pytest`, boundary checker).

---

## Architecture & Bounded Context Alignment

Per `AGENTS.md` and `scripts/check_boundaries.py`:
- **Context boundary rule**: `registry`, `runtime`, `governance`, `observability`, and `identity` cannot import directly from each other.
- **Shared kernel**: Database connection, Base models, and session utilities live strictly inside `apps/api/src/shared/`.
- Domain models are placed in `apps/api/src/shared/db/models/`:
  - `shared/db/models/agent.py`: `Agent` and `AgentVersion`
  - `shared/db/models/run.py`: `Run`
  - `shared/db/models/span.py`: `Span`
  - `shared/db/models/__init__.py`: re-exports all models so Alembic's `Base.metadata` detects all tables.

---

## Detailed Data Model

### 1. `agents` Table
- `id`: UUID (Primary Key, generated via `uuid.uuid4`)
- `name`: String(64), unique, non-null, indexed (slug format matching spec)
- `description`: Text, nullable
- `owner`: String(255), non-null (owner email)
- `stage`: String(32), non-null, default `"draft"` (`draft`, `prototype`, `staging`, `production`, `deprecated`, `retired`)
- `current_version`: String(32), nullable
- `created_at`: DateTime(timezone=True), non-null, default UTC
- `updated_at`: DateTime(timezone=True), non-null, default UTC, onupdate UTC

### 2. `agent_versions` Table (Immutable Spec Snapshots)
- `id`: UUID (Primary Key)
- `agent_id`: UUID, Foreign Key -> `agents.id` (ON DELETE CASCADE), non-null, indexed
- `version`: String(32), non-null (e.g. `"0.3.0"`)
- `spec`: JSON / JSONB, non-null (full raw validated `AgentSpec` dict snapshot)
- `created_at`: DateTime(timezone=True), non-null, default UTC
- **Constraints**: `UniqueConstraint("agent_id", "version", name="uq_agent_versions_agent_id_version")`

### 3. `runs` Table
- `id`: UUID (Primary Key)
- `agent_id`: UUID, Foreign Key -> `agents.id` (ON DELETE CASCADE), non-null, indexed
- `agent_version_id`: UUID, Foreign Key -> `agent_versions.id` (ON DELETE SET NULL), nullable, indexed
- `status`: String(32), non-null, default `"pending"` (`pending`, `running`, `completed`, `failed`, `cancelled`, `waiting_approval`)
- `trigger_type`: String(32), non-null, default `"manual"` (`manual`, `schedule`, `webhook`)
- `input`: JSON / JSONB, nullable (run input parameters)
- `output`: JSON / JSONB, nullable (agent output payload)
- `error`: Text, nullable (failure diagnostics)
- `started_at`: DateTime(timezone=True), nullable
- `completed_at`: DateTime(timezone=True), nullable
- `cost_usd`: Float, non-null, default 0.0
- `total_tokens`: Integer, non-null, default 0
- `created_at`: DateTime(timezone=True), non-null, default UTC
- `updated_at`: DateTime(timezone=True), non-null, default UTC, onupdate UTC

### 4. `spans` Table (OTLP Trace Spans)
- `id`: UUID (Primary Key)
- `run_id`: UUID, Foreign Key -> `runs.id` (ON DELETE CASCADE), non-null, indexed
- `trace_id`: String(64), non-null, indexed (OTel trace identifier)
- `span_id`: String(64), non-null, indexed (OTel span identifier)
- `parent_span_id`: String(64), nullable, indexed
- `name`: String(255), non-null (e.g. `"llm_call"`, `"tool_call:web-fetch"`)
- `kind`: String(32), non-null, default `"INTERNAL"`
- `start_time`: DateTime(timezone=True), non-null
- `end_time`: DateTime(timezone=True), nullable
- `status`: String(32), non-null, default `"UNSET"` (`OK`, `ERROR`, `UNSET`)
- `attributes`: JSON / JSONB, nullable, default `{}` (GenAI semantic conventions & `varistha.*`)
- `events`: JSON / JSONB, nullable, default `[]`
- `created_at`: DateTime(timezone=True), non-null, default UTC
