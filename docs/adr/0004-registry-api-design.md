# ADR 0004: Agent Registry API Design & Spec Immutability

## Status
Accepted

## Context
In Phase 1, Task 3 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 3` & `§ 3.4, § 4.2`), we must provide HTTP API endpoints to create, list, and retrieve agents and their version snapshots. Key architectural constraints include:
1. Bounded Context: All registry logic must live in `apps/api/src/registry/` without cross-context dependencies into `runtime/`, `governance/`, `observability/`, or `identity/`.
2. Spec Integrity: Agent specifications submitted to the API must be rigorously validated against `packages/spec` before persistence.
3. Immutability: Once an agent version is published, its specification snapshot is immutable. Any attempt to modify or overwrite an existing version must be rejected.
4. Identifiers: Agents must be addressable both by internal UUID and human-readable unique slug names (`metadata.name`).

## Decision

### 1. Endpoint Architecture (`/api/v1/agents`)
We established REST endpoints in `apps/api/src/registry/router.py`:
- `POST /api/v1/agents`: Validates raw JSON spec with `packages/spec.validate_spec()`. If the agent does not exist, registers the agent and publishes version `0.1.0` (or specified version). If the agent exists, publishes a new version if not already existing. Returns HTTP 201 on creation, HTTP 422 with structured field error paths on invalid spec, and HTTP 409 on duplicate version.
- `GET /api/v1/agents`: Lists agents with pagination (`limit`, `offset`) and filtering (`stage`, `owner`).
- `GET /api/v1/agents/{id_or_name}`: Resolves agent by UUID or unique slug name, returning agent metadata and current version spec.
- `GET /api/v1/agents/{id_or_name}/versions`: Returns historical version list (chronological, newest first).
- `GET /api/v1/agents/{id_or_name}/versions/{version}`: Returns the exact immutable `AgentSpec` dictionary snapshot for the given version.
- `POST /api/v1/agents/{id_or_name}/versions`: Publishes a new version directly on an existing agent. Rejects mismatched `metadata.name` with HTTP 400, invalid specs with HTTP 422, and duplicate versions with HTTP 409.

### 2. Service Layer & Database Isolation
We decoupled router logic from database access via `apps/api/src/registry/service.py`:
- `resolve_agent(session, id_or_name)`: Checks if string is a valid UUID; if so, queries by primary key, otherwise queries by unique `name`.
- `create_or_update_agent(session, raw_spec)`: Handles atomic creation of `Agent` and initial `AgentVersion`, or attaching a new immutable version.
- `list_agents(session, stage, owner, limit, offset)`: Efficient filtered count and pagination query.
- `get_version(session, agent_id, version)` / `list_versions(session, agent_id)`: Fetches version records with immutable JSON spec payload.

### 3. Pydantic Response Schemas
In `apps/api/src/registry/schemas.py`:
- `AgentResponse`: Public agent summary with version count and timestamps.
- `AgentDetailResponse`: Extends `AgentResponse` with `latest_spec` payload.
- `AgentListResponse`: Paginated envelope with items, total, limit, and offset.
- `AgentVersionSummaryResponse` & `AgentVersionDetailResponse`: Version summaries and full spec snapshot.
- All schemas use runtime imports (`uuid`, `datetime`) to guarantee compatibility with Pydantic v2 reflection.

### 4. Async Test Strategy & Greenlet Coverage Concurrency
- Configured isolated in-memory SQLite fixtures (`sqlite+aiosqlite:///:memory:`) using `StaticPool` and `httpx.AsyncClient(transport=ASGITransport(app=app))`.
- Added `[tool.coverage.run] concurrency = ["greenlet", "thread"]` to `pyproject.toml` so coverage.py accurately traces async execution across SQLAlchemy 2.0 greenlet context switches.

## Consequences

### Positive
- Strict input validation prevents malformed or unversioned agents from entering the database.
- Immutability guarantee prevents runtime drift across agent executions.
- Zero cross-context import violations: only depends on `shared/` kernel and `packages/spec`.
- Full 100% test coverage across all `registry/` modules.

### Negative / Trade-offs
- Overwriting a version requires incrementing the semver tag; hotfixes must be versioned (by design).
