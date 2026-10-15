# Milestone Checkpoint: Phase 1, Task 8 — Minimal UI (`apps/ui`)

- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 8 — Minimal UI: agents list, runs list, and trace view
- **Status**: PASSED
- **Timestamp**: 2026-10-15T16:30:00+05:30
- **Git Commit**: `ae6179c`
- **Reference Spec**: `docs/SPEC.md § 7.5 Task 8 & § 4.4 & § 5`

---

## 1. Implemented Capabilities

1. **Frontend Application & Design System (`apps/ui/src/`)**:
   - `lib/types.ts`: TypeScript strict models for `Agent`, `AgentVersion`, `Run`, `Span`, `TraceDetailResponse`, `AgentStage`, `RunStatus`, `AutonomyLevel`.
   - `lib/api.ts`: Typed API client handling connection errors, HTTP errors, health check, agent queries, run triggers, and span queries.
   - `components/navbar.tsx`: Sticky navigation bar with brand icon, links to `/agents` and `/runs`, real-time API health status indicator, and repository link.
   - `components/badges.tsx`: Semantic `StageBadge` (Draft, Prototype, Staging, Production, Deprecated, Retired), `StatusBadge` (completed, running with CSS pulse, failed, waiting_approval), and `AutonomyBadge` (`L0` - `L3`).
   - `components/empty-state.tsx`, `components/loading-skeleton.tsx`, `components/error-alert.tsx`: Dedicated loading, empty, and error feedback states for all screens per `SPEC.md § 4.4`.
   - `components/trigger-run-modal.tsx`: Modal dialog for validating input JSON payloads, selecting trigger types (`manual`, `schedule`, `webhook`), executing runs, and redirecting to the trace view.

2. **Custom Trace Waterfall (`components/trace-waterfall.tsx`)**:
   - Computes trace boundaries and relative offsets `(offsetMs / totalDurationMs) * 100%`.
   - Renders hierarchical span rows with indentations and duration percentage bars (with minimum 6px width for microsecond visibility).
   - Semantic span categorization (root workflow, LLM call, tool call, guardrail, error).
   - Interactive span inspection drawer displaying attributes (`gen_ai.request.model`, `gen_ai.usage.total_tokens`, `varistha.cost_usd`, etc.).

3. **Pages**:
   - `app/agents/page.tsx` & `app/page.tsx`: Agents registry table with stage badges, autonomy tags, search filter, stage tabs, and run trigger actions.
   - `app/runs/page.tsx`: Operational runs list with status badges, token usage, cost attribution, timestamp, and trace links.
   - `app/runs/[id]/page.tsx`: Run detail view with metric cards (duration, tokens, cost, span count), error alerts, embedded `TraceWaterfall`, and input/output payload inspectors.

4. **API Backend Enhancements (`apps/api`)**:
   - `apps/api/src/main.py`: Added `CORSMiddleware` allowing Next.js dev server (`http://localhost:3000`) and browser clients.
   - `apps/api/src/runtime/service.py`: Added `list_all_runs` querying runs across agents with optional `agent_id` and `status` filters.
   - `apps/api/src/runtime/router.py`: Exposed `GET /api/v1/runs` endpoint with pagination and filtering.

---

## 2. Test & Quality Metrics

- **UI Tests Added**: 17 Vitest tests in `apps/ui/src/__tests__/` (`badges.test.tsx`, `feedback.test.tsx`, `trace-waterfall.test.tsx`, `smoke.test.ts`).
- **Python Backend Tests**: 164 tests passing across monorepo (`test_list_all_runs_and_filters` added).
- **Backend Test Coverage**: 97% overall coverage across `apps/api`, `packages/`, and `plugins/`.
- **Next.js Production Build**: Turbopack production build succeeded cleanly with 0 errors (`next build`).
- **Linter Status**: `pnpm run lint` clean (0 errors, 0 warnings); `ruff check` clean (0 errors).
- **Format Status**: `ruff format --check` clean (0 errors).
- **Type Checker Status**: `pnpm typecheck` clean (0 errors); `pyright` strict clean (0 errors, 0 warnings).
- **Architecture Boundaries**: `check_boundaries.py` clean (0 cross-context violations).
- **Architectural Decision Record**: `docs/adr/0009-minimal-ui-architecture-and-waterfall.md`.

---

## 3. Artifact Manifest

- `apps/ui/src/lib/types.ts`: UI domain types and interfaces.
- `apps/ui/src/lib/api.ts`: API client.
- `apps/ui/src/components/badges.tsx`: Stage, status, and autonomy badges.
- `apps/ui/src/components/empty-state.tsx`: Empty state component.
- `apps/ui/src/components/loading-skeleton.tsx`: Table and waterfall skeletons.
- `apps/ui/src/components/error-alert.tsx`: Error alert component.
- `apps/ui/src/components/navbar.tsx`: Global navigation header.
- `apps/ui/src/components/trigger-run-modal.tsx`: Run trigger modal dialog.
- `apps/ui/src/components/trace-waterfall.tsx`: Custom Gantt trace waterfall component.
- `apps/ui/src/app/layout.tsx`: Root layout with Navbar and semantic theme.
- `apps/ui/src/app/page.tsx`: Root page mounting Agents view.
- `apps/ui/src/app/agents/page.tsx`: Agents list and search view.
- `apps/ui/src/app/runs/page.tsx`: Runs list and filter view.
- `apps/ui/src/app/runs/[id]/page.tsx`: Run detail and trace waterfall view.
- `apps/ui/src/__tests__/badges.test.tsx`: Badge component tests.
- `apps/ui/src/__tests__/feedback.test.tsx`: Empty, skeleton, and error component tests.
- `apps/ui/src/__tests__/trace-waterfall.test.tsx`: Trace waterfall tests.
- `apps/api/src/main.py`: CORS middleware.
- `apps/api/src/runtime/service.py`: `list_all_runs` implementation.
- `apps/api/src/runtime/router.py`: `GET /api/v1/runs` endpoint.
- `apps/api/src/runtime/tests/test_router.py`: `test_list_all_runs_and_filters`.
- `docs/adr/0009-minimal-ui-architecture-and-waterfall.md`: Architecture Decision Record.
- `docs/plans/phase-1-task-8-ui.md`: Plan artifact.
