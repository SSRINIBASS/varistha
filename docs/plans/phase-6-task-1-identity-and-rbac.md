# Plan: Phase 6 Task 1 — Identity & Multi-User RBAC System

## 1. Context & Objectives
In accordance with `docs/SPEC.md § 5 (Phase 6)`, implement authentication and multi-user role-based access control (RBAC):
- Roles: `admin`, `operator`, `viewer`.
- API Key authentication via `X-API-Key` or `Authorization: Bearer <key>`.
- Admin can manage agents, promote to prod, change policies, and manage keys.
- Operator can run agents, review/approve approval items, and trigger evals.
- Viewer has read-only access to agents, traces, and metrics.
- Seamless developer mode: if `AUTH_ENABLED=false` (default for local dev/testing), requests have default admin privileges. If `AUTH_ENABLED=true` or an API key is provided, strict verification is enforced.

## 2. Files to Touch / Create
1. `apps/api/src/shared/db/models/identity.py`: SQLAlchemy model for `ApiKeyRecord` with secure SHA-256 hash storage.
2. `apps/api/alembic/versions/0006_identity_and_api_keys.py`: Migration for `api_keys` table.
3. `apps/api/src/identity/schemas.py`: Pydantic request/response schemas for API keys.
4. `apps/api/src/identity/service.py`: Service for secure token generation (`var_live_...`), constant-time hash verification, and key lifecycle.
5. `apps/api/src/identity/dependencies.py`: FastAPI security dependencies (`require_role`, `get_current_identity`).
6. `apps/api/src/identity/router.py`: REST routes (`POST /api/v1/auth/keys`, `GET /api/v1/auth/keys`, `DELETE /api/v1/auth/keys/{key_id}`).
7. `apps/api/src/main.py`: Register auth router under `/api/v1/auth`.
8. `apps/api/src/identity/tests/test_auth.py`: Tests for token issuance, role-based protection, revocation, and dev fallback.

## 3. Risks & Architectural Boundaries
- Bounded Context: `apps/api/src/identity/` must not import other domain packages (`registry`, `runtime`, `governance`, `observability`).
- All modules < 300 lines.
- Pyright clean, Ruff clean, 100% green tests.
