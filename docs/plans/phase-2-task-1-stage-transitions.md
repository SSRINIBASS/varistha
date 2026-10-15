# Plan: Phase 2, Task 1 — Stage Transitions, Promotion Gates & Immutable Audit Log

> **For Agent:** Implement Phase 2 Task 1 per `AGENTS.md` and `docs/SPEC.md § 3.2, § 5`.

**Goal:** Implement robust lifecycle stage progression (`Draft` → `Prototype` → `Staging` → `Production` → `Deprecated` → `Retired`) enforced by verifiable gate evaluators, preventing unverified agents from reaching production, and capturing an immutable audit log for every transition.

**Architecture:** 
- A new database model `StageTransition` and table `stage_transitions` linked to `agents` with an Alembic migration.
- A decoupled, modular gate evaluation engine in `apps/api/src/registry/gates.py` checking spec compliance, run history, eval definitions, guardrails, budgets, and operational checks.
- Service methods in `apps/api/src/registry/service.py` for dry-run gate checking, executing promotions, and retrieving audit histories.
- REST endpoints in `apps/api/src/registry/router.py`: `POST /api/v1/agents/{id_or_name}/promote`, `GET /api/v1/agents/{id_or_name}/history`, and `GET /api/v1/agents/{id_or_name}/gates/{target_stage}`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, pytest-asyncio.

---

## 1. Specification & Gate Rules (`docs/SPEC.md § 3.2`)

| Transition | Gate Checklist |
| :--- | :--- |
| **Draft → Prototype** | 1. Spec validates schema<br>2. Agent has run successfully at least once (`status == "success"`) |
| **Prototype → Staging** | 1. Owner email assigned and non-empty<br>2. Guardrails attached (`input`, `output`, or `tools` guardrails present)<br>3. Eval suite exists and `min_pass_rate` defined |
| **Staging → Production** | 1. Eval score meets threshold on current version<br>2. At least N (>=1) reviewed/successful runs<br>3. Budget limits set (`max_usd_per_run` > 0 and `max_usd_per_day` > 0)<br>4. Kill switch verified / operational confirmation |
| **Production → Deprecated** | 1. Replacement agent named or migration rationale provided<br>2. Traffic drained (no runs currently in `running` or `pending` status) |
| **Deprecated → Retired** | 1. Triggers disabled/empty<br>2. History preserved (runs and audit log present)<br>3. Secrets revocation confirmed |
| **Demotions / Rollbacks** | Allowed (e.g. `Production` → `Staging`, `Staging` → `Prototype`) with mandatory audit reason. |

---

## 2. Files to Create and Modify

### New Files
1. `apps/api/src/shared/db/models/stage_transition.py` — `StageTransition` SQLAlchemy model.
2. `apps/api/alembic/versions/0002_stage_transitions.py` — Alembic migration script for `stage_transitions` table.
3. `apps/api/src/registry/gates.py` — Pure domain gate evaluators and transition rules.
4. `apps/api/src/registry/tests/test_gates.py` — Unit tests for individual gate checks and transitions.
5. `apps/api/src/registry/tests/test_promotion.py` — Integration tests for promotion, gate dry-runs, and audit log endpoints.
6. `docs/adr/0009-stage-promotion-gates.md` — ADR documenting lifecycle gate architecture.
7. `docs/plans/phase-2-task-1-stage-transitions.md` — In-repo plan archive.

### Modified Files
1. `apps/api/src/shared/db/models/__init__.py` — Export `StageTransition`.
2. `apps/api/src/shared/db/models/agent.py` — Add `stage_transitions` relationship to `Agent`.
3. `apps/api/src/registry/schemas.py` — Add Pydantic request/response schemas for promotion and history.
4. `apps/api/src/registry/service.py` — Add `evaluate_gates`, `promote_agent`, and `get_stage_history`.
5. `apps/api/src/registry/router.py` — Add endpoints for `/promote`, `/history`, and `/gates/{target_stage}`.

---

## 3. Step-by-Step Implementation

### Step 1: Database Model & Alembic Migration
- Define `StageTransition` with columns:
  - `id`: UUID (PK)
  - `agent_id`: UUID (FK `agents.id`, ON DELETE CASCADE, indexed)
  - `from_stage`: String(32)
  - `to_stage`: String(32)
  - `promoted_by`: String(255)
  - `reason`: Text (nullable)
  - `gate_results`: JSON/JSONB
  - `created_at`: DateTime(timezone=True)
- Create migration `0002_stage_transitions.py` with `upgrade()` and `downgrade()`.
- Run `uv run alembic upgrade head` to verify migration on SQLite.

### Step 2: Gate Evaluation Engine (`apps/api/src/registry/gates.py`)
- Define `LifecycleStage` literal: `"draft" | "prototype" | "staging" | "production" | "deprecated" | "retired"`.
- Implement dataclasses / Pydantic models:
  - `GateCheck`: `name: str`, `passed: bool`, `message: str`
  - `GateResult`: `allowed: bool`, `checks: list[GateCheck]`
- Implement gate functions:
  - `evaluate_draft_to_prototype(agent, latest_spec, runs) -> GateResult`
  - `evaluate_prototype_to_staging(agent, latest_spec, runs) -> GateResult`
  - `evaluate_staging_to_production(agent, latest_spec, runs, options) -> GateResult`
  - `evaluate_production_to_deprecated(agent, latest_spec, runs, options) -> GateResult`
  - `evaluate_deprecated_to_retired(agent, latest_spec, runs, options) -> GateResult`
- Write comprehensive unit tests in `test_gates.py`.

### Step 3: Service Layer Integration (`apps/api/src/registry/service.py`)
- Define exceptions:
  - `InvalidStageTransitionError`
  - `GateCheckFailedError`
- Implement `promote_agent(session, id_or_name, request)`:
  - Resolves agent and fetches latest version spec and runs.
  - Checks if transition is valid.
  - If promotion, executes gate evaluator. If gate fails, raises `GateCheckFailedError`.
  - Updates `agent.stage = to_stage`.
  - Creates and commits `StageTransition` audit record.
- Implement `get_stage_history(session, agent_id)` returning audit records.
- Implement `check_gates_preview(session, id_or_name, target_stage)` for dry-run inspection.

### Step 4: Schemas & API Endpoints
- In `schemas.py`:
  - `PromoteAgentRequest(to_stage, promoted_by, reason, replacement, kill_switch_verified, secrets_revoked)`
  - `GateCheckResponse(name, passed, message)`
  - `StageTransitionResponse(...)`
  - `PromoteAgentResponse(agent, transition, checks)`
- In `router.py`:
  - `POST /api/v1/agents/{id_or_name}/promote` → 200 on success, 422 on gate failure with gate results, 400 on invalid transition.
  - `GET /api/v1/agents/{id_or_name}/history` → 200 with chronological list.
  - `GET /api/v1/agents/{id_or_name}/gates/{target_stage}` → 200 with dry-run checklist.

### Step 5: Verification & Quality Gates
- Run test suite: `uv run pytest apps/api/src/registry/tests/ -v`.
- Run linters: `uv run ruff check .` and `uv run ruff format --check .`.
- Run type-checker: `uv run pyright apps/ packages/`.
- Run architecture boundary validator: `uv run python scripts/check_boundaries.py`.
- Run full test suite across monorepo to guarantee no regressions.

---

## 4. Risks & Mitigations

- **Risk:** Existing demo agent in dev DB has `stage: "prototype"`.
  - **Mitigation:** Alembic migration only adds `stage_transitions` table, preserving existing agents and runs without data loss.
- **Risk:** Staging to Production requires kill switch verification.
  - **Mitigation:** Allow explicit `kill_switch_verified: true` in the promotion request payload to verify that the operator has tested or confirmed the kill switch.
