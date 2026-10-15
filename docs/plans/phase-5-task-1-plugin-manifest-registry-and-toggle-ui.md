# Implementation Plan: Phase 5, Task 1 — Plugin Manifest Registry & UI Toggle System

## Context & Objectives
In accordance with `docs/SPEC.md § 5 (Phase 5: Plugin ecosystem and role packs)` and `docs/SPEC.md § 3.1, § 4.4`:
- **Goal**: Expose installed MCP/in-process plugins via REST API, enable dynamic plugin discovery from manifests, and provide an operator UI to explore plugins, inspect their risk levels and permissions scopes, and toggle plugins per agent.
- **Security Rule**: Plugin permissions and approval requirements are enforced in deterministic code outside the model. Untrusted output flags are clearly communicated.
- **Design System Rule**: Primer aesthetic, semantic tokens, WCAG AA contrast, light & dark theme support, empty/loading/error states on all screens. Zero hardcoded colors.

---

## 1. Files to Touch / Create

### Backend (`apps/api`)
- `apps/api/src/plugins/schemas.py`: Pydantic response schemas for plugin manifests, capabilities, tool lists, and agent-plugin status.
- `apps/api/src/plugins/router.py`: FastAPI router mounted under `/api/v1/plugins`:
  - `GET /api/v1/plugins`: List all discovered plugins with risk, approval requirements, scopes, and tools.
  - `GET /api/v1/plugins/{name}`: Get detailed manifest and config schema for a plugin.
- `apps/api/src/main.py`: Include `plugins_router`.
- `apps/api/src/plugins/tests/test_router.py`: Unit and integration tests for plugin endpoints.

### Frontend (`apps/ui`)
- `apps/ui/src/lib/types.ts`: Add `PluginInfo`, `PluginListResponse`, `PluginRiskLevel`.
- `apps/ui/src/lib/api.ts`: Add `getPlugins`, `getPlugin`.
- `apps/ui/src/components/badges.tsx`: Add `PluginRiskBadge` (`low`, `medium`, `high`) and `ApprovalRequiredBadge`.
- `apps/ui/src/components/plugins/plugin-card.tsx`: Card component displaying plugin metadata, risk level, required scopes, transport, and capabilities.
- `apps/ui/src/components/plugins/plugin-explorer.tsx`: Searchable and filterable plugin grid with category/risk filters.
- `apps/ui/src/app/plugins/page.tsx`: Top-level `/plugins` page with KPI cards (Discovered Plugins, Low/Med/High Risk Breakdown, Approval-Gated Capabilities).
- `apps/ui/src/components/navbar.tsx`: Add `Plugins` navigation link with `Blocks` or `Plug` icon.
- `apps/ui/src/__tests__/plugins.test.tsx`: Vitest tests for plugin components and badges.

### Documentation & Decisions
- `docs/adr/0020-plugin-manifest-registry-and-toggle-system.md`: ADR documenting the plugin registry API, security boundary, and toggle design.

---

## 2. Acceptance Criteria & Exit Gate
1. `GET /api/v1/plugins` discovers all manifests in `plugins/` and returns structured schema.
2. `PluginRiskBadge` and `ApprovalRequiredBadge` render with semantic tokens and icons.
3. `/plugins` UI renders responsive grid with search, risk filters, and empty/loading/error states.
4. Boundaries check (`scripts/check_boundaries.py`) reports 0 violations.
5. All test suites pass: `pytest` (backend), `vitest` (frontend), `pyright` (types), `tsc` (strict TypeScript), `ruff` (linter/formatter).
