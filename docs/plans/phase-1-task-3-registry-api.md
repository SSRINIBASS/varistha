# Plan: Phase 1, Task 3 — Registry API Endpoints

## Task Restatement & Goal

- **Task**: API endpoints to create, list and get agents and versions (`docs/SPEC.md § 7.5 Task 3` & `§ 3.4, § 4.2`).
- **Goal**: Implement the RESTful Registry API in FastAPI allowing users, the CLI (`varistha apply`), and the UI to register agents from declarative `AgentSpec`s, list agents with stage and owner filtering, retrieve agent details, and access immutable version histories.
- **Exit Criteria**:
  - `POST /api/v1/agents` validates incoming specs using `packages/spec`, inserts or updates `Agent`, and creates immutable `AgentVersion`.
  - `GET /api/v1/agents` lists registered agents with pagination (`limit`, `offset`) and filtering (`stage`, `owner`).
  - `GET /api/v1/agents/{id_or_name}` fetches an agent by UUID or unique slug name.
  - `GET /api/v1/agents/{id_or_name}/versions` lists all version snapshots for an agent.
  - `GET /api/v1/agents/{id_or_name}/versions/{version}` retrieves a specific immutable version spec snapshot.
  - `POST /api/v1/agents/{id_or_name}/versions` registers a new version for an existing agent (rejecting duplicate versions with 409 Conflict).
  - Integration tests in `apps/api/src/registry/tests/test_router.py` verifying all endpoints, status codes, and error cases (200, 201, 404, 409, 422).
  - Test coverage ≥ 80%, all linters and type-checkers clean, architecture boundaries respected.

---

## Architecture & Boundaries

- **Bounded Context**: `apps/api/src/registry/`.
- **Allowed Imports**:
  - `shared.db` (`get_db_session`, `Agent`, `AgentVersion`).
  - `spec` (`AgentSpec`, `validate_spec`, `SpecValidationError`).
  - FastAPI / Starlette / Pydantic.
- **Prohibited**: Direct imports of `runtime`, `governance`, `observability`, or provider SDKs.

---

## Endpoints Specification

| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/v1/agents` | 201 / 409 / 422 | Create an agent or publish a new version from an `AgentSpec` payload |
| `GET` | `/api/v1/agents` | 200 | List agents with optional `stage`, `owner` filters, and pagination |
| `GET` | `/api/v1/agents/{id_or_name}` | 200 / 404 | Get agent by UUID or slug name with latest version summary |
| `GET` | `/api/v1/agents/{id_or_name}/versions` | 200 / 404 | List historical version snapshots for an agent |
| `GET` | `/api/v1/agents/{id_or_name}/versions/{version}` | 200 / 404 | Get exact immutable version spec snapshot |
| `POST` | `/api/v1/agents/{id_or_name}/versions` | 201 / 409 / 422 | Publish an explicit new version for an existing agent |

---

## Files to Touch / Create

1. **`apps/api/src/registry/schemas.py`**:
   - Pydantic response and request models: `AgentResponse`, `AgentDetailResponse`, `AgentListResponse`, `AgentVersionResponse`, `AgentVersionSummaryResponse`.
2. **`apps/api/src/registry/service.py`**:
   - Database query and mutation operations with async sessions:
     - `resolve_agent(session, id_or_name)` -> Agent
     - `list_agents(session, stage, owner, limit, offset)` -> list[Agent]
     - `create_agent_from_spec(session, spec)` -> tuple[Agent, AgentVersion]
     - `create_version_for_agent(session, agent, spec)` -> AgentVersion
     - `get_version(session, agent_id, version)` -> AgentVersion
3. **`apps/api/src/registry/router.py`**:
   - FastAPI `APIRouter(prefix="/api/v1/agents", tags=["agents"])`.
   - Error handlers translating `SpecValidationError` to 422, duplicate versions to 409, not found to 404.
4. **`apps/api/src/registry/__init__.py`**:
   - Re-export router.
5. **`apps/api/src/main.py`**:
   - Include `registry_router`.
6. **`apps/api/src/registry/tests/test_router.py`**:
   - Integration tests with `httpx.AsyncClient`:
     - Register agent from fixture YAML/dict -> 201 Created.
     - Validation failure -> 422 Unprocessable Entity with structured error array.
     - Duplicate version creation -> 409 Conflict.
     - List agents and filter by stage/owner.
     - Get agent by UUID and get agent by slug name -> 200 OK.
     - Non-existent agent -> 404 Not Found.
     - Get version history and specific version spec -> 200 OK.
7. **Documentation**:
   - `docs/plans/phase-1-task-3-registry-api.md`: Persistent plan copy.
   - `docs/adr/0004-registry-api-design.md`: Architecture decision record for registry REST contracts.
   - `docs/checkpoints/2026-10-15-phase-1-task-3-registry-api.md`: Completion checkpoint with test metrics.
   - `CHANGELOG.md`: Updated with Task 3 additions.

---

## Verification Plan

1. `uv run pytest apps/api/src/registry/tests/ -v` passes with ≥ 80% coverage.
2. Full pytest suite passes (`uv run pytest`).
3. `uv run ruff check .` and `uv run ruff format --check .` clean.
4. `uv run pyright apps/ packages/` clean.
5. `uv run python scripts/check_boundaries.py` clean.
