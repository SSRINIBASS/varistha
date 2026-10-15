# ADR 0013: Approval Workflow, Human Runtime Interrupts, and Payload Diffing

## Status
Accepted

## Context
Per `docs/SPEC.md § 3.1` (Autonomy Levels L0-L4), `§ 3.3` (Governance: Human Runtime Interrupts and Approval Requirements), and `§ 5` (Phase 3 Milestones), autonomous AI agents must not perform unverified outbound actions (e.g., sending emails, publishing social media posts, writing to CRMs, or executing external webhooks) without explicit human oversight when configured at autonomy levels `L0` (Full Human Approval) or `L1` (Human in the Loop for Outbound).

Furthermore, the Varistha Security Rules explicitly mandate:
1. Outbound actions require approval at autonomy L1 and below. No code path may bypass this.
2. Tool permissions, rate limits, and approval requirements must be enforced in code **outside the model**.
3. Operators must be able to inspect the proposed payload, approve, reject, or edit the payload with a structured field-level diff recorded for auditability.
4. An OpenTelemetry trace span `approval.wait` must be emitted whenever an agent run enters a waiting state.

## Decision

### 1. Database Entity and Schema Migration
- Created the `Approval` model in `apps/api/src/shared/db/models/approval.py` within the shared persistence kernel:
  - `id`: UUID primary key.
  - `run_id`: Foreign key to `runs.id` (cascade delete).
  - `agent_id`: Foreign key to `agents.id` (cascade delete).
  - `status`: String enum (`pending`, `approved`, `rejected`, `edited`).
  - `action_type`: String (e.g. `outbound.email`, `outbound.crm`, `tool.execute`).
  - `proposed_payload`: JSON dictionary representing the model's intended action parameters.
  - `approved_payload`: Optional JSON dictionary representing modified or accepted parameters.
  - `payload_diff`: Optional JSON dictionary recording structured field-level differences.
  - `operator_feedback`: Optional string with instructions or rationale from the human operator.
  - `resolved_by`: Optional identifier of the human operator.
  - `created_at`, `resolved_at`: UTC timestamps.
- Added Alembic migration `0003_approvals.py` using `sa.JSON().with_variant(postgresql.JSONB, "postgresql")` ensuring full compatibility with both SQLite (for lightweight testing and local runs) and PostgreSQL (for production).

### 2. Runtime Interception Outside the Model
- In `apps/api/src/runtime/adapter.py`, the `LangGraphRuntime.execute()` engine inspects:
  - Agent autonomy level (`L0` requires approval for all non-readonly actions; `L1` requires approval for outbound/destructive keywords).
  - Plugin tool manifests for tools explicitly declared with `requires_approval: true`.
- If triggered, execution halts **outside the model**, setting `approval_required=True` and populating `proposed_action` with `tool_name`, `action_type`, and `parameters`.
- The runtime emits an OpenTelemetry span named `approval.wait` under the active run trace, attaching attributes:
  - `varistha.approval_required`: `True`
  - `varistha.approval_status`: `"pending"`
  - `varistha.action_type`: `action_type`
- In `apps/api/src/runtime/service.py`, the run transitions to `RunStatus.WAITING_APPROVAL` with `completed_at=None`, and an `Approval` record is persisted.

### 3. Field-Level JSON Payload Diffing
- Implemented `compute_payload_diff(proposed, approved) -> dict[str, Any]` in `apps/api/src/governance/approvals/service.py`:
  - Recursively compares nested dictionaries, arrays, and primitive values.
  - Categorizes changes into `added`, `removed`, and `modified` (with `old` and `new` value comparisons).
  - Returns an empty dictionary when payloads match identically.

### 4. Operator Resolution Service and API Endpoints
- Provided `apps/api/src/governance/approvals/` within the `governance` bounded context:
  - `GET /api/v1/approvals`: List pending or resolved approvals with filtering by status and agent ID.
  - `GET /api/v1/approvals/{id}`: Detailed view including proposed payload, approved payload, diff, and execution metadata.
  - `POST /api/v1/approvals/{id}/resolve`: Accepts `action` (`approve`, `reject`, `edit`), optional `edited_payload`, `feedback`, and `operator_id`.
    - If `edit`: Verifies edited payload presence, computes payload diff, updates `approved_payload`, sets status to `edited`, and completes the run.
    - If `approve`: Adopts proposed payload directly and marks run `completed`.
    - If `reject`: Records feedback and marks run `failed`.

### 5. CLI Management Interface
- Added `varistha approvals` commands under `packages/cli/src/varistha_cli/commands/approvals_cmd.py`:
  - `varistha approvals list [--status <pending|approved|rejected|edited>]`: Renders a Rich table of approvals.
  - `varistha approvals get <id>`: Displays proposed payload and status details.
  - `varistha approvals approve <id> [--feedback <text>]`: Approves proposed action.
  - `varistha approvals reject <id> [--reason <text>]`: Rejects action and aborts run.
  - `varistha approvals edit <id> --payload '<json>' [--feedback <text>]`: Modifies payload and displays computed diff.

## Consequences

### Positive
- Strict enforcement of autonomy L0 and L1 guarantees that autonomous agents cannot execute outbound side-effects without explicit human authorization.
- Bounded context separation is preserved: `governance` owns approval resolution and payload diffing, while `runtime` handles interception without importing `governance` internal logic.
- Complete auditability: All payload modifications and operator rationales are stored alongside OpenTelemetry trace spans.

### Negative
- Interrupted runs remain in `waiting_approval` status until an operator intervenes, requiring polling, webhooks, or UI notifications for operator queues.
