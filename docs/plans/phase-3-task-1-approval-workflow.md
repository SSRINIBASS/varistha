# Plan: Phase 3, Task 1 — Approval Workflow, Human Interrupts & Audit Diff

> **For Agent:** Implement Phase 3 Task 1 per `AGENTS.md` and `docs/SPEC.md § 3.1, § 3.3, § 5`.

**Goal:** Implement human-in-the-loop approval workflows with runtime execution interrupts:
1. When an agent operating at autonomy `L1` or lower attempts an outbound action (or invokes any tool marked `requires_approval: true`), execution is paused outside the model.
2. An `approval` request is persisted, setting the run to `waiting_approval` and emitting an `approval.wait` OpenTelemetry span.
3. Operators can inspect, approve, reject, or edit-and-approve the proposed action via REST API and CLI.
4. When edited, the system computes and records the payload diff and feedback signal for model evaluation.
5. Upon resolution, the runtime resumes execution with the approved payload or marks the run failed if rejected.

---

## 1. Specification & Requirements (`docs/SPEC.md § 3.1, § 3.3, § 5`)

- **Autonomy Levels:**
  - `L0 Suggest`: Agent proposes, human acts.
  - `L1 Act with approval`: Agent acts only after human approval (default for outbound actions).
  - Outbound actions (email, social posts, CRM writes) require approval at autonomy `L1` and below. **No code path may bypass this.**
- **Exit Criteria for Phase 3:**
  - *"An outbound action is impossible without approval at L1, and a runaway agent is stopped by its budget."*
- **Bounded Context Rule:**
  - Placed under `apps/api/src/governance/` (clean separation from `registry/`, `runtime/`, `observability/`).
  - Runtime interacts with governance via clean interfaces and database records.

---

## 2. Files to Create and Modify

### New Files
1. `apps/api/src/shared/db/models/approval.py` — SQLAlchemy model for `Approval`.
2. `apps/api/alembic/versions/0003_approvals.py` — Alembic migration for `approvals` table.
3. `apps/api/src/governance/` — Bounded context package:
   - `apps/api/src/governance/__init__.py`
   - `apps/api/src/governance/schemas.py` — Pydantic models for approvals list, detail, and resolution.
   - `apps/api/src/governance/service.py` — Core domain logic: create approval, list, resolve, compute diff.
   - `apps/api/src/governance/router.py` — FastAPI REST endpoints.
   - `apps/api/src/governance/tests/test_approvals_service.py` — Unit tests for approval logic and diff computation.
   - `apps/api/src/governance/tests/test_approvals_api.py` — Integration tests for REST endpoints.
4. `packages/cli/src/varistha_cli/approvals.py` — CLI subcommands (`varistha approvals list`, `get`, `approve`, `reject`).
5. `packages/cli/tests/test_approvals_cli.py` — CLI test suite.
6. `docs/adr/0013-approval-workflow-and-runtime-interrupts.md` — ADR documenting approval state machine and diffing engine.
7. `docs/plans/phase-3-task-1-approval-workflow.md` — Implementation plan.

### Modified Files
1. `apps/api/src/shared/db/models/__init__.py` — Export `Approval`.
2. `apps/api/src/shared/db/models/run.py` — Add `approvals` relationship to `Run`.
3. `apps/api/src/main.py` — Register governance router under `/api/v1/approvals`.
4. `apps/api/src/runtime/adapter.py` — Intercept tool calls requiring approval at autonomy L1 or manifest `requires_approval`.
5. `packages/cli/src/varistha_cli/main.py` — Register `approvals` CLI group.

---

## 3. Database Schema

`approvals` table:
- `id`: UUID (PK)
- `run_id`: UUID (FK `runs.id`, ON DELETE CASCADE, indexed)
- `agent_id`: UUID (FK `agents.id`, ON DELETE CASCADE, indexed)
- `status`: String(32) — `pending`, `approved`, `rejected`, `edited` (indexed)
- `action_type`: String(64) — e.g. `tool_call`, `outbound_action`
- `tool_name`: String(128), nullable
- `proposed_payload`: JSON
- `approved_payload`: JSON, nullable
- `diff`: JSON, nullable (field-level delta between proposed and edited)
- `feedback`: Text, nullable
- `reviewer`: String(255), nullable
- `created_at`: DateTime(timezone=True)
- `resolved_at`: DateTime(timezone=True), nullable

---

## 4. API Endpoints

- `GET /api/v1/approvals`: List approvals with status, agent_id, and run_id filtering.
- `GET /api/v1/approvals/{id}`: Fetch single approval details with payloads.
- `POST /api/v1/approvals/{id}/resolve`:
  - Body: `{ decision: "approve" | "reject" | "edit", payload?: dict, feedback?: string, reviewer: string }`
  - When `decision == "edit"`, computes field delta between `proposed_payload` and `payload`, marks status as `edited`, and sets `approved_payload`.
  - Resumes or terminates associated run.

---

## 5. Verification Plan

1. **Unit Tests:**
   - Test approval state machine: pending -> approved, pending -> rejected, pending -> edited.
   - Test payload diff generator on nested structures and scalar values.
2. **Integration Tests:**
   - Test REST API endpoints with valid/invalid payloads, missing IDs, unauthorized statuses.
3. **Runtime Test:**
   - Execute run for agent at L1 calling an outbound tool: verify run status changes to `waiting_approval` and pending approval record is created.
   - Resolve approval: verify run status advances to `completed` with the approved payload.
4. **CLI Tests:**
   - Test `varistha approvals list`, `get`, `approve`, and `reject`.
5. **Full Suite Regression:**
   - `uv run pytest` (214+ tests passing), `pnpm test` (all UI tests passing), `scripts/check_boundaries.py` clean.
