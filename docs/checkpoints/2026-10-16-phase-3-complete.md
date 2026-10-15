# Checkpoint: Phase 3 Complete — Governance & Boundaries

**Date:** 2026-10-16  
**Tag:** `phase-3-complete`  
**Phase:** Phase 3 (Approvals, Guardrails, and Budgets)  
**Status:** PASS  

---

## 1. Executive Summary

Phase 3 of Varistha delivers the human-in-the-loop and automated safety boundaries that distinguish an enterprise AI Employee Control Plane from an unmonitored script. Before Phase 3, agents could execute actions and incur API costs without programmatic limits or human oversight.

With Phase 3 complete:
1. **Outbound Actions Require Approval at Autonomy L0/L1:** The runtime interrupts execution whenever an agent proposes an outbound action (email, social post, external webhook, CRM mutation). An `Approval` record is created, execution enters `waiting_approval`, and OpenTelemetry emits an `approval.wait` trace span.
2. **Financial & Cost Protection:** Agents enforce per-run spend ceilings (`max_usd_per_run`) and daily rolling UTC budget caps (`max_usd_per_day`). Breaching either aborts or blocks runs.
3. **Emergency Circuit Breakers:** Per-agent kill switches and a platform-wide Global Emergency Stop allow operators to halt all agent activity instantly.
4. **Deterministic Outside-the-Model Guardrails:** Input and output policies (`pii-redact`, `injection-scan`, `schema-valid`, `no-unverified-claims`) intercept data outside the model, preventing prompt injection attacks and redacting sensitive PII before execution.
5. **Governance Control Room UI:** A full-width GitHub Primer-inspired dashboard at `/governance` gives operators a human-in-the-loop approvals inbox with unified parameter diffs, an interactive budget and circuit breaker manager, and a live guardrail testing sandbox.

---

## 2. Exit Criteria Verification (`docs/SPEC.md § 5`)

| Exit Criterion | Implementation & Evidence | Status |
| :--- | :--- | :---: |
| **An outbound action is impossible without approval at autonomy L1** | Implemented `apps/api/src/runtime/adapter.py` and `service.py`. When an agent at L0 or L1 invokes an outbound tool or action flagged `requires_approval: true`, the runtime halts, enters `waiting_approval`, records an `Approval` entity in the database, and pauses execution until an operator explicitly approves or edits & approves via API/UI/CLI. Verified by automated test `test_runtime_adapter_interrupts_outbound_action_at_l1`. | **PASS** |
| **A runaway agent is stopped by its budget** | Implemented `apps/api/src/governance/budgets/service.py` and runtime interceptor. When daily spend reaches `max_usd_per_day`, run initiation is blocked with HTTP 429 (`BudgetExceededError`). When an individual run's spend exceeds `max_usd_per_run`, the run is aborted with status `failed`. Verified by automated tests `test_trigger_agent_run_blocked_when_daily_budget_exhausted` and `test_trigger_agent_run_aborted_when_single_run_cost_exceeds_max_usd_per_run`. | **PASS** |
| **Emergency circuit breakers halt execution immediately** | Implemented agent-level kill switch and global emergency stop in `SystemSetting`. Tripped kill switches immediately reject runs with HTTP 409 (`KillSwitchTrippedError`). Verified by automated tests `test_trigger_agent_run_blocked_when_agent_kill_switch_tripped` and `test_trigger_agent_run_blocked_when_global_emergency_stop_active`. | **PASS** |
| **Untrusted data cannot compromise system prompts or leak PII** | Implemented `shared/guardrails/` policy engine. Pre-flight input scanning blocks prompt injection attacks with HTTP 422 (`PolicyViolationError`) and redacts PII before runtime invocation. Output guardrails enforce schema conformity. Verified by automated tests `test_trigger_run_blocked_by_injection_guardrail`, `test_trigger_run_pii_redaction_before_execution`, and `test_trigger_run_output_guardrail_blocks_invalid_schema`. | **PASS** |
| **Operator UI provides complete governance oversight** | Created `apps/ui/src/app/governance/page.tsx` with Approvals Inbox (filtering, detail drawer, GitHub-style parameter diff viewer, approve/reject/edit actions), Budgets & Circuit Breakers board, and Guardrails Explorer with live interactive test sandbox. Verified by 9 Vitest unit tests in `governance.test.tsx` and end-to-end browser verification. | **PASS** |

---

## 3. Architecture & Security Compliance

- **Boundaries (`AGENTS.md` & `scripts/check_boundaries.py`):**
  - Zero cross-context imports between `registry/`, `runtime/`, `governance/`, `observability/`, and `identity/`.
  - Shared kernel (`apps/api/src/shared/guardrails/`) provides core policy abstractions used by both `runtime` and `governance`.
- **Security & Autonomy:**
  - All approvals, budgets, and guardrail decisions are evaluated in deterministic code outside the LLM.
  - Secret keys, passwords, and PII are redacted from traces and logs (`apps/api/src/shared/telemetry/redaction.py`).
  - Web fetching plugins strictly block private and loopback address ranges (SSRF protection).
- **Design System:**
  - Primer aesthetic strictly observed: no hardcoded colors, dark and light theme support, semantic tokens.

---

## 4. Test Suite & Code Quality Metrics

| Gate Check | Result | Standard | Status |
| :--- | :--- | :--- | :---: |
| **Pytest Unit & Integration Tests** | 146 / 146 passed | 100% passing | **PASS** |
| **Python Code Coverage** | 92.29% (4,332 statements) | &ge; 80% per module | **PASS** |
| **Pyright Strict Type Checking** | 0 errors, 0 warnings | Clean | **PASS** |
| **Ruff Linter & Formatter** | Clean | All checks passed | **PASS** |
| **Vitest UI Component Tests** | 32 / 32 passed | 100% passing | **PASS** |
| **TypeScript Strict (`tsc --noEmit`)** | 0 errors | Clean | **PASS** |
| **ESLint (Next.js & React 19)** | 0 errors, 0 warnings | Clean | **PASS** |
| **Next.js Production Build** | Clean build (Turbopack) | Clean | **PASS** |
| **Bandit Security Scan** | 0 medium / high issues | Clean | **PASS** |
| **Architecture Boundaries Check** | 0 violations | Clean | **PASS** |
| **GitHub Actions CI & Code Review** | 4/4 workflows green | 100% green | **PASS** |

---

## 5. Artifacts & Deliverables

1. **Alembic Migrations:**
   - `0003_approvals.py`: Created `approvals` table.
   - `0004_budgets_and_killswitch.py`: Extended `agents` table with kill switch flags and created `system_settings` table.
2. **Governance Domain (`apps/api/src/governance/`):**
   - `approvals/`: Approval schemas, services with recursive JSON diff engine, and REST endpoints.
   - `budgets/`: Spend calculations, daily budget limits, agent kill/resume switches, and global emergency stop.
   - `policies/`: Registered policies metadata and interactive policy test endpoints.
3. **Guardrails Engine (`apps/api/src/shared/guardrails/`):**
   - Core interfaces (`PolicyHook`, `PolicyAction`, `PolicyResult`, `PolicyEngine`).
   - Built-in policies: `pii-redact`, `injection-scan`, `schema-valid`, `no-unverified-claims`.
4. **Runtime Middleware (`apps/api/src/runtime/`):**
   - Outbound approval interruption at autonomy L0/L1.
   - Financial circuit breaker aborts on `max_usd_per_run` and blocks on `max_usd_per_day`.
   - Pre-flight input guardrail filtering and post-flight output schema verification.
5. **CLI Tooling (`packages/cli/`):**
   - `varistha approvals list`, `get`, `approve`, `reject`, `edit`.
   - `varistha policies list`, `test`.
6. **Governance Web UI (`apps/ui/`):**
   - Route: `/governance`.
   - `ApprovalsInbox`, `PayloadDiffViewer`, `BudgetsDashboard`, `GuardrailsExplorer`.
7. **ADRs:**
   - `docs/adr/0013-approval-workflow-and-runtime-interrupts.md`
   - `docs/adr/0014-budget-tracking-and-circuit-breakers.md`
   - `docs/adr/0015-guardrail-policy-engine-and-middleware.md`
   - `docs/adr/0016-governance-dashboard-ui-and-approvals.md`
