# ADR 0014: Budget Tracking, Rate Limiting, and Emergency Kill Switch Circuit Breakers

## Status
Accepted

## Context
Per `docs/SPEC.md § 3.1` (Autonomy Levels L0-L4), `§ 3.3` (Governance: Budgets, Rate Limits, and Circuit Breakers), and `§ 5` (Phase 3 Milestones), autonomous AI agents must operate within deterministic financial and operational boundaries.

Specifically:
1. Every Agent Spec declares budget ceilings: `spec.budget.max_usd_per_run` and `spec.budget.max_usd_per_day`.
2. Runaway executions that exceed the per-run budget ceiling must be terminated immediately **outside the model**, transitioning to status `failed` with error message `budget_exceeded: Run cost ($X) exceeded limit ($Y)` and emitting OpenTelemetry span attribute `varistha.budget.exceeded = True`.
3. The platform must prevent new runs if accumulated spend in the current UTC rolling window meets or exceeds `max_usd_per_day`, returning HTTP 429 Too Many Requests (`BudgetExceededError`).
4. Both granular (per-agent) and platform-wide (global emergency stop) kill switches must halt agent execution immediately without requiring redeployment or model cooperation, returning HTTP 409 Conflict (`KillSwitchTrippedError`).
5. OpenTelemetry traces must record `varistha.kill_switch_tripped = True` when blocked.

## Decision

### 1. Database Schema Extensions and Persistence Kernel
- **Agent Model Updates (`apps/api/src/shared/db/models/agent.py`)**:
  - `is_active: bool` (default `True`): Controls active agent status.
  - `kill_switch_tripped: bool` (default `False`): Circuit-breaker trip status.
  - `kill_switch_reason: str | None`: Audit justification for kill action.
  - `kill_switch_tripped_at: datetime | None`: Timestamp when kill switch engaged.
- **System Settings Model (`apps/api/src/shared/db/models/setting.py`)**:
  - Stores dynamic control plane configuration including `global_kill_switch` state with fields `enabled`, `reason`, `tripped_at`, and `operator`.
- **Alembic Migration (`0004_budgets_and_killswitch.py`)**:
  - Uses `op.batch_alter_table("agents")` for SQLite compatibility during local development while maintaining clean PostgreSQL schema transitions.

### 2. Governance Budget & Kill Switch Service (`apps/api/src/governance/budgets/`)
- Isolated within the `governance` bounded context (zero imports from `runtime` context):
  - `get_daily_spend(session, agent_id)`: Queries `runs` table for all non-failed runs starting in UTC today (`run.created_at >= start_of_day_utc`), aggregating `run.cost_usd`.
  - `get_agent_budget_status(session, agent)`: Resolves active version spec, daily spend, remaining daily budget, per-run limit, and kill switch state.
  - `trip_agent_kill_switch(session, agent, reason, operator)`: Disables agent (`is_active=False`, `kill_switch_tripped=True`) and records audit metadata.
  - `resume_agent(session, agent, operator)`: Reactivates agent and clears circuit breaker state.
  - `get_global_kill_switch(session)` & `set_global_kill_switch(session, enabled, reason, operator)`: Manages platform-wide emergency stop state.
  - `check_pre_flight_budget_and_kill_switch(session, agent, spec)`: Evaluates pre-run permissions.
  - `check_post_run_budget_breaker(spec, cost_usd)`: Enforces hard per-run USD cap.

### 3. Runtime Circuit Breaker Interception
- In `apps/api/src/runtime/service.py`:
  - `trigger_agent_run` executes pre-flight checks:
    - Global kill switch check: aborts with `KillSwitchTrippedError` (HTTP 409) if platform emergency stop is active.
    - Agent kill switch check: aborts with `KillSwitchTrippedError` (HTTP 409) if agent switch tripped or inactive.
    - Daily budget check: aborts with `BudgetExceededError` (HTTP 429) if daily accumulated spend ≥ `max_usd_per_day`.
  - Tags root OTel span with `varistha.kill_switch_tripped = True` or `varistha.budget.exceeded = True`.
- In `apps/api/src/runtime/adapter.py`:
  - In `LangGraphRuntime.execute()`, after step execution or simulated cost accumulation, compares `result_state["cost_usd"]` against `spec.budget.max_usd_per_run`.
  - If exceeded, overrides status to `RunStatus.FAILED`, setting `error="budget_exceeded: Run cost ($X) exceeded limit ($Y)"` and tags span with `varistha.budget.exceeded = True`.

### 4. Telemetry Semantic Conventions
- Defined constants in `apps/api/src/shared/telemetry/conventions.py`:
  - `VARISTHA_BUDGET_EXCEEDED = "varistha.budget.exceeded"`
  - `VARISTHA_KILL_SWITCH_TRIPPED = "varistha.kill_switch_tripped"`

### 5. CLI Interface (`packages/cli/`)
- Added Click commands:
  - `varistha budget <agent>`: Displays Rich table or JSON view of daily spend, limits, remaining budget, and switch states.
  - `varistha kill <agent> [--reason <reason>] [--operator <id>]`: Trips agent kill switch immediately.
  - `varistha resume <agent> [--operator <id>]`: Restores agent execution.
  - `varistha emergency-stop [--enable|--disable] [--reason <reason>] [--operator <id>]`: Inspects or toggles platform-wide emergency stop.

## Consequences
- Guaranteed financial safety: runaway agent steps cannot drain funds beyond the configured per-run limit.
- Zero-latency operational intervention: operators can halt runaway agents or the entire platform instantly through REST API or CLI.
- Clean bounded contexts maintained: runtime and governance interact solely through shared models and public schemas, with no cyclic or cross-domain package dependencies.
