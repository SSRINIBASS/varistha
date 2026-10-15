# ADR 0009: Minimal UI Architecture, Custom Trace Waterfall, and Design System

## Status
Accepted

## Context
Phase 1, Task 8 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 8` & `§ 4.4`) requires a minimal web dashboard in `apps/ui` that delivers operational visibility into AI employees:
1. **Agents Registry View (`/agents` and `/`)**: Listing registered agents, their lifecycle stage (`draft`, `prototype`, `staging`, `production`), autonomy level, version, and providing an interactive run trigger dialog.
2. **Execution Runs Monitor (`/runs`)**: Listing historical and active execution runs across agents, with filter capabilities (by status and agent), token counts, and cost attribution.
3. **Trace Waterfall View (`/runs/[id]`)**: Visualizing OpenTelemetry spans in a custom Gantt-style timeline with duration bars, hierarchical indentations, and an interactive span attribute inspector.
4. **Design System Adherence (`SPEC.md § 4.4`)**: Semantic design tokens, light/dark themes with WCAG AA contrast, pairing colors with icons, dense typography (14px base), and dedicated loading skeletons, empty states, and error alerts on every screen.

## Decision

### 1. Technology Selection: Next.js App Router, Tailwind CSS v4, and Vitest
- **Next.js 16 App Router (React 19)**: Selected for modern server/client component streaming, partial prerendering (`ppr`), clean route segmentation, and TypeScript strict mode.
- **Tailwind CSS v4 with CSS Variable Design Tokens**: All styles adhere to CSS theme variables (`--background`, `--foreground`, `--primary`, `--muted`, `--border`, `--destructive`), completely avoiding hardcoded hex colors.
- **Vitest & React Testing Library**: Fast in-memory unit and component testing (`environment: jsdom`), validating rendering, user interactions, and state progressions.

### 2. Design System Components (`apps/ui/src/components/`)
- **Semantic Badges (`badges.tsx`)**:
  - `StageBadge`: Encapsulates canonical lifecycle stages (Draft, Prototype, Staging, Production, Deprecated, Retired) with paired icons (`Layers`, `Sparkles`, `Clock`, `ShieldCheck`, `AlertTriangle`, `Archive`).
  - `StatusBadge`: Maps execution statuses (completed, running with CSS pulse animation, failed, waiting_approval).
  - `AutonomyBadge`: Visual indicators for `L0` through `L3` with descriptive tooltips.
- **Feedback & Resilience**:
  - `EmptyState`: Contextual empty views guiding users to CLI actions (`varistha init`, `varistha apply`).
  - `TableSkeleton` & `WaterfallSkeleton`: Non-blocking shimmer skeletons for perceived performance.
  - `ErrorAlert`: Actionable error messages with a retry callback.
- **Trigger Run Modal (`trigger-run-modal.tsx`)**: Interactive dialog for validating JSON payloads, selecting trigger types, and executing runs directly from the browser.

### 3. Custom Trace Waterfall Timeline (`trace-waterfall.tsx`)
- Standard charting libraries lack support for nested OpenTelemetry span graphs with relative millisecond offsets and rich attribute inspection.
- The custom `TraceWaterfall` component:
  1. Computes absolute trace boundaries (`traceStartMs`, `totalDurationMs`).
  2. Calculates relative span start offsets `(offsetMs / totalDurationMs) * 100%`.
  3. Renders proportional duration bars with a minimum width (6px) ensuring fast microsecond spans remain clickable.
  4. Visualizes parent-child hierarchy via indentations and `ChevronRight` markers.
  5. Categorizes spans by semantic kind (workflow root, LLM call, tool call, guardrail check, error).
  6. Provides an interactive attribute inspector displaying runtime parameters (`gen_ai.request.model`, `gen_ai.usage.total_tokens`, `varistha.cost_usd`, etc.).

### 4. API Integration & CORS
- Added `CORSMiddleware` in `apps/api/src/main.py` allowing cross-origin requests from the Next.js frontend (`http://localhost:3000`).
- Added `GET /api/v1/runs` endpoint in `apps/api/src/runtime/` supporting pagination and filtering by `agent_id` and `status`.

## Consequences

### Positive
- Completes the final acceptance milestone for Phase 1: an agent YAML file applied via CLI can be executed, and the resulting run and its full trace waterfall are inspectable in the web UI.
- Strict design system compliance: zero hardcoded colors, high accessibility contrast, responsive layouts.
- High test coverage: 17 UI component tests in Vitest and 164 monorepo tests in Pytest passing cleanly.

### Negative / Trade-offs
- The Next.js client currently polls on manual refresh rather than a WebSocket/SSE push stream; push streaming is slated for later phases.
