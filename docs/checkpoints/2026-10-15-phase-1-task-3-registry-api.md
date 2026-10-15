# Milestone Checkpoint: Phase 1, Task 3 — Registry API Endpoints

- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 3 — API endpoints to create, list, and get agents and versions
- **Status**: PASSED
- **Timestamp**: 2026-10-15T13:45:00+05:30
- **Git Commit**: `520dbab`
- **Reference Spec**: `docs/SPEC.md § 3.4, § 4.2 & § 7.5 Task 3`

---

## 1. Implemented Capabilities

1. **Registry Schemas (`apps/api/src/registry/schemas.py`)**:
   - `AgentResponse`: Public summary representation containing id, slug name, description, owner, stage, current_version, version count, and UTC timestamps.
   - `AgentDetailResponse`: Detailed agent payload containing the current version's full `AgentSpec` snapshot dictionary.
   - `AgentListResponse`: Paginated response model with items, total count, limit, and offset.
   - `AgentVersionSummaryResponse`: Version identifier, semver tag, and publication timestamp.
   - `AgentVersionDetailResponse`: Complete snapshot with immutable `spec` dictionary.
   - `ValidationErrorDetail`: Error format reporting structured field locations for spec validation failures.

2. **Registry Service Layer (`apps/api/src/registry/service.py`)**:
   - `resolve_agent()`: Dual lookup supporting either UUID string or unique slug name.
   - `create_or_update_agent()`: Validates spec with `packages/spec`, inserts `Agent` and initial `AgentVersion`, or appends a new immutable version. Rejects duplicate version attempts with `DuplicateVersionError`.
   - `list_agents()`: Filtered queries by lifecycle stage (`prototype`, `staging`, `production`, `deprecated`) and owner email, with pagination and total count.
   - `get_version()` and `list_versions()`: Immutable snapshot retrieval.

3. **FastAPI Endpoints (`apps/api/src/registry/router.py`)**:
   - `POST /api/v1/agents`: Validates spec and registers agent or publishes new version (201 Created, 422 Unprocessable Content on validation errors, 409 Conflict on duplicate version).
   - `GET /api/v1/agents`: Lists agents with query filtering by `stage` and `owner`.
   - `GET /api/v1/agents/{id_or_name}`: Retrieves agent details by UUID or slug name (404 on missing).
   - `GET /api/v1/agents/{id_or_name}/versions`: Lists versions for an agent.
   - `GET /api/v1/agents/{id_or_name}/versions/{version}`: Retrieves exact immutable spec snapshot.
   - `POST /api/v1/agents/{id_or_name}/versions`: Publishes new version directly on an existing agent.

4. **Package Spec Convenience Export (`packages/spec/src/spec.py`)**:
   - Provides clean root imports `from spec import AgentSpec, validate_spec, SpecValidationError`.

---

## 2. Test & Quality Metrics

- **Integration Tests Added (`apps/api/src/registry/tests/test_router.py`)**: 13 comprehensive integration tests.
- **Cumulative Tests**: 54 passing tests across the monorepo.
- **Test Coverage**:
  - `apps/api/src/registry/router.py`: 100%
  - `apps/api/src/registry/service.py`: 100%
  - `apps/api/src/registry/schemas.py`: 100%
  - `apps/api/src/registry/__init__.py`: 100%
  - Overall repository coverage: 99% (exceeds ≥ 80% requirement).
- **Linter Status**: `ruff check` clean (0 errors).
- **Format Status**: `ruff format --check` clean (0 errors).
- **Type Checker Status**: `pyright` strict clean (0 errors, 0 warnings).
- **Architecture Boundaries**: `OK: All architecture boundaries respected.` (0 cross-context violations).
- **Architectural Decision Record**: `docs/adr/0004-registry-api-design.md`.

---

## 3. Artifact Manifest

- `apps/api/src/registry/schemas.py`: Pydantic response models.
- `apps/api/src/registry/service.py`: Registry business logic & DB queries.
- `apps/api/src/registry/router.py`: API route endpoints under `/api/v1/agents`.
- `apps/api/src/registry/__init__.py`: Package export exposing router.
- `apps/api/src/main.py`: Mounted registry router into application.
- `apps/api/src/registry/tests/conftest.py`: In-memory SQLite async test fixture.
- `apps/api/src/registry/tests/test_router.py`: 13 integration tests for router endpoints.
- `packages/spec/src/spec.py`: Canonical exports for `spec` package.
- `docs/plans/phase-1-task-3-registry-api.md`: Implementation plan.
- `docs/adr/0004-registry-api-design.md`: ADR documenting registry design decisions.
- `docs/checkpoints/2026-10-15-phase-1-task-3-registry-api.md`: This milestone checkpoint.

---

## 4. Known Gaps & Next Steps

- **Current State**: Phase 1 Task 1 (Spec), Task 2 (Database & Alembic), and Task 3 (Registry API) are complete and passing.
- **Next Task**: Phase 1 Task 4 — Implement mock Runtime adapter and `POST /api/v1/agents/{id}/runs` endpoint to trigger an execution (`docs/SPEC.md § 7.5 Task 4`).
