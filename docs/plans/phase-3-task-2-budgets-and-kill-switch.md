# Plan: Phase 3, Task 2 — Budget Tracking, Rate Limiting & Kill Switch Circuit Breaker

> **Mission:** Implement Phase 3 Task 2 per `AGENTS.md` and `docs/SPEC.md § 3.1, § 3.3, § 4.2, § 5`.
> **Exit Criterion:** *"A runaway agent is stopped by its budget."*

---

## 1. Context & Objectives

Per `docs/SPEC.md § 3.3` (Governance & Run Control), `§ 3.4` (Spec BudgetConfig), and `§ 5` (Phase 3 Milestones):
1. **Per-Run Budget Limit (`max_usd_per_run`):** If a single run's accumulated USD cost exceeds the spec limit, execution halts immediately outside the model, transitioning the run to `failed` with error `budget_exceeded: Run cost ($X) exceeded limit ($Y)`.
2. **Daily Rolling Budget Limit (`max_usd_per_day`):** Before executing a run, the system computes the agent's accumulated spend across the current UTC calendar day / 24h window. If the limit is reached or exceeded, new runs and LLM calls are blocked.
3. **Rate Limiting:** Enforce maximum run and tool invocation velocity (e.g. `rate-limit-50-per-day` declared in `spec.guardrails.tools`).
4. **Kill Switch Circuit Breaker:**
   - **Per-Agent Kill Switch:** Immediate shutdown toggle (`is_active=False` or `kill_switch_tripped=True`) on the `Agent` model. Halts in-flight execution and blocks any new trigger invocations.
   - **Global Kill Switch:** System-wide emergency stop halting all agent executions across the entire control plane.
5. **OpenTelemetry Telemetry:** Emits `varistha.budget.exceeded`, `varistha.kill_switch_tripped`, and records `varistha.budget.cost_usd` vs `varistha.budget.max_usd_per_run` / `max_usd_per_day`.
6. **API & CLI:** REST endpoints under `/api/v1/agents/{id}/budget`, `/api/v1/agents/{id}/kill`, `/api/v1/agents/{id}/resume`, and CLI commands `varistha budget`, `varistha kill`, `varistha resume`.

---

## 2. Bounded Context & Architecture

- **Bounded Context Rule:**
  - `governance/budgets/` owns budget calculations, rate limit auditing, and kill-switch state.
  - `shared/` kernel provides database models (`Agent` kill switch column, `SystemSetting` or kill switch flag).
  - `runtime/` consults budget/kill-switch policy before execution and enforces per-run circuit breaker without importing internal `governance` business logic (decoupled via clean interfaces/contracts).
  - No cross-context imports between `governance/`, `registry/`, `runtime/`, `observability/`, and `identity/`.

---

## 3. Files to Create and Modify

### New Files
1. `apps/api/alembic/versions/0004_budgets_and_killswitch.py` — Alembic migration adding `is_active` and `kill_switch_tripped` (with reason and timestamp) to `agents` table.
2. `apps/api/src/governance/budgets/schemas.py` — Pydantic schemas: `AgentBudgetStatusResponse`, `KillSwitchRequest`, `KillSwitchResponse`, `GlobalKillSwitchStatus`.
3. `apps/api/src/governance/budgets/service.py` — Core domain logic:
   - `get_daily_spend(session, agent_id) -> float`
   - `check_run_budget_limits(session, agent, spec) -> BudgetCheckResult`
   - `trip_agent_kill_switch(session, agent_id, reason, operator) -> Agent`
   - `resume_agent(session, agent_id, operator) -> Agent`
   - `set_global_kill_switch(active, reason) -> bool`
4. `apps/api/src/governance/budgets/router.py` — REST API endpoints for budget inspection and kill-switch control.
5. `apps/api/src/governance/tests/test_budgets_service.py` — Unit tests for spend aggregation, budget threshold breaches, and kill switch logic.
6. `apps/api/src/governance/tests/test_budgets_api.py` — Integration tests for budget & kill-switch REST endpoints.
7. `apps/api/src/runtime/tests/test_runtime_budget_breaker.py` — Integration test verifying runaway agents are aborted when exceeding `max_usd_per_run` or `max_usd_per_day`.
8. `packages/cli/src/varistha_cli/commands/budget_cmd.py` — CLI commands: `varistha budget <agent>`, `varistha kill <agent>`, `varistha resume <agent>`.
9. `packages/cli/tests/test_budget_cli.py` — CLI unit tests.
10. `docs/adr/0014-budget-tracking-and-circuit-breakers.md` — Architectural Decision Record.

### Modified Files
1. `apps/api/src/shared/db/models/agent.py` — Add `is_active: bool = True`, `kill_switch_tripped: bool = False`, `kill_switch_reason: str | None`, `kill_switch_tripped_at: datetime | None`.
2. `apps/api/src/runtime/service.py` — Pre-flight kill switch and daily budget gate; post-execution per-run budget breaker with OTel span tagging.
3. `apps/api/src/runtime/adapter.py` — Per-run cost monitoring during execution loop.
4. `apps/api/src/governance/router.py` — Mount budget and kill-switch routers.
5. `packages/cli/src/varistha_cli/client.py` — Add client methods for budget and kill-switch API calls.
6. `packages/cli/src/varistha_cli/display.py` — Rich table formatting for budget status and kill-switch alerts.
7. `packages/cli/src/varistha_cli/main.py` — Register `budget_cmd` and kill/resume commands.
8. `CHANGELOG.md` — Document Phase 3 Task 2 deliverable.

---

## 4. Verification & Quality Gates

1. **Unit & Integration Tests:**
   - Budget calculation accurately aggregates 24h spend.
   - Run immediately rejected when daily budget is exhausted.
   - Run aborted with status `failed` and clear message when single run exceeds `max_usd_per_run`.
   - Tripping kill switch prevents new runs from starting.
   - Global emergency stop halts all agents.
   - CLI commands render proper Rich UI for budgets, kill, and resume.
2. **Quality Gates:**
   - `uv run ruff check apps/ packages/ plugins/` (clean)
   - `uv run pyright` (0 errors, 0 warnings)
   - `python scripts/check_boundaries.py` (0 boundary violations)
   - `uv run pytest` (100% passing, &ge; 80% coverage per module)
   - `pnpm test` (apps/ui suite passing)
