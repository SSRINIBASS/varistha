# Implementation Plan: Phase 1, Task 8 — Minimal UI (Agents, Runs, and Trace View)

## 1. Task Objective & Context
- **Reference**: `docs/SPEC.md § 7.5 Task 8`, `§ 4.4 (UI and design system)`, and `§ 5 (Phase 1 Exit Criteria)`.
- **Goal**: Implement the Next.js control plane interface in `apps/ui` providing:
  1. **Agents List (`/` and `/agents`)**: View all registered agents, stage badges, autonomy levels, current versions, trigger runs, and inspect specs.
  2. **Runs List (`/runs`)**: Monitor execution runs across agents with status badges, token usage, cost attribution, and trace links.
  3. **Trace Waterfall View (`/runs/[id]/trace` or `/traces/[id]`)**: High-fidelity custom waterfall timeline displaying root `agent.run` and child `llm.call` spans, duration bars, and span attribute inspector.
- **Phase 1 Exit Gate**: A YAML spec applied via CLI becomes an agent, executes a run, and is fully inspectable in the UI with an end-to-end trace view.

---

## 2. Architecture & Design Rules (`SPEC.md § 4.4`)
- **Framework & Libraries**: Next.js 15+ App Router, TypeScript strict mode, Tailwind CSS v4, Lucide icons, Vitest + React Testing Library.
- **Design Tokens & Theme**:
  - Semantic stage badges: `Draft` (neutral/zinc), `Prototype` (blue/sky), `Staging` (violet/purple), `Production` (emerald/green), `Deprecated` (amber/orange), `Retired` (slate).
  - Semantic status badges: `completed` (green), `running` (blue pulse), `failed` (red), `waiting_approval` (amber/yellow).
  - WCAG AA contrast, light & dark theme via existing CSS tokens.
  - Consistent layout: 14px base typography, dense 36-40px table rows, calm whitespace.
  - Every screen must implement **Loading Skeleton**, **Empty State**, and **Error State** with retry.

---

## 3. Scope of Changes

### A. API Enhancements (`apps/api`)
1. **CORS Middleware (`apps/api/src/main.py`)**: Enable `CORSMiddleware` to allow requests from `http://localhost:3000` (Next.js default port) and configurable allowed origins.
2. **Global Runs Endpoint (`apps/api/src/runtime/`)**:
   - `service.py`: Add `list_all_runs(session, agent_id=None, status=None, limit=50, offset=0)` querying the `runs` table with optional agent/status filters.
   - `router.py`: Expose `GET /api/v1/runs` returning `RunListResponse`.
   - `test_router.py`: Add tests for `GET /api/v1/runs` with pagination and status filters.

### B. UI Client & Types (`apps/ui/src/lib/`)
1. **`api.ts`**: Clean HTTP client for control plane endpoints:
   - `getAgents()`, `getAgent(idOrName)`, `getAgentVersions(idOrName)`
   - `getRuns(params?)`, `getAgentRuns(idOrName, params?)`, `getRun(runId)`
   - `triggerRun(idOrName, input, triggerType)`
   - `getRunSpans(runId)`, `getTraceSpans(traceId)`
   - `checkHealth()`
2. **`types.ts`**: TypeScript strict interfaces matching backend schemas:
   - `Agent`, `AgentVersion`, `Run`, `Span`, `TraceDetail`, `HealthStatus`.

### C. Components & Design Primitives (`apps/ui/src/components/`)
1. **Navigation (`components/navbar.tsx`)**:
   - Top navigation bar with Varistha logo, links to **Agents** and **Runs**, API health indicator pill, and theme toggle.
2. **Badges (`components/badges.tsx`)**:
   - `StageBadge`: Renders stage with semantic color and icon (Draft, Prototype, Staging, Production, Deprecated, Retired).
   - `StatusBadge`: Renders run status with semantic color and animated pulse for `running`.
   - `AutonomyBadge`: Renders autonomy level (`L0` - `L3`) with tooltips.
3. **State Feedback Components**:
   - `components/empty-state.tsx`: Generic empty state with title, description, and action button.
   - `components/loading-skeleton.tsx`: Table and waterfall skeleton loaders.
   - `components/error-alert.tsx`: Error display with retry trigger.
4. **Trigger Run Modal (`components/trigger-run-modal.tsx`)**:
   - Dialog allowing user to provide input JSON/text and trigger a run, redirecting directly to the run trace.
5. **Trace Waterfall (`components/trace-waterfall.tsx`)**:
   - Computes relative timeline positions (`start_time - trace_start`) and duration percentages.
   - Displays nested span rows (operation name, duration ms, service/component tag, status indicator).
   - Interactive selection: clicking a span shows the **Span Details Inspector** side panel with full attributes, timestamps, and metadata.

### D. App Pages (`apps/ui/src/app/`)
1. **Root & Agents List (`app/page.tsx` & `app/agents/page.tsx`)**:
   - Table of all registered agents with columns: Agent Name, Role summary, Stage, Autonomy, Version, Updated, Actions (Trigger Run, View Runs).
2. **Runs List (`app/runs/page.tsx`)**:
   - Table of execution runs with columns: Run ID, Agent, Status, Trigger, Tokens, Cost ($USD), Duration, Created At, Link to Trace.
3. **Run Detail & Trace View (`app/runs/[id]/page.tsx`)**:
   - Run summary header: Agent name, status, tokens breakdown (prompt/completion/total), cost, duration.
   - Embedded `TraceWaterfall` component with span attribute drawer.
   - Run inputs & outputs inspection tab/panel.

---

## 4. Test Strategy (`apps/ui`)
- Unit and component tests using Vitest + React Testing Library:
  1. `badges.test.tsx`: Tests rendering of all stage badges and status badges.
  2. `agents.test.tsx`: Tests agents list loading skeleton, empty state, and populated table.
  3. `runs.test.tsx`: Tests runs list loading, empty state, filtering, and cost/token formatting.
  4. `trace-waterfall.test.tsx`: Tests waterfall calculation (bar widths, offsets), span click inspection, and attributes rendering.
  5. API integration tests in `apps/api/src/runtime/tests/test_router.py` verifying `GET /api/v1/runs`.

---

## 5. Risks & Mitigation
- **CORS Issues in Dev**: Handled by adding `CORSMiddleware` in `apps/api/src/main.py`.
- **Clock Drift / Zero Duration Spans**: Microsecond-fast spans could render with 0px width; mitigated by setting a minimum visual width (e.g., 4px) for bars so all spans are visible and clickable.
- **SSR / Hydration Mismatch**: Use `'use client'` on interactive views or standard data-fetching patterns in App Router.
