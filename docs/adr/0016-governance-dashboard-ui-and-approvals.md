# ADR 0016: Governance UI Control Room, Approvals Reviewer, Budgets, and Guardrails Explorer

## Status
Accepted

## Context
Per `docs/SPEC.md § 3.3` (Governance & Approvals), `§ 4.4` (UI and Design System), and `§ 5` (Phase 3 Milestone: Approvals UI & Governance Dashboard), startup operators must have a centralized control plane to review pending outbound actions, inspect budgets and spend ceilings, manage circuit breakers, and test guardrail policies.

Prior to this task:
1. Approvals, budgets, and guardrail policies were accessible only via HTTP REST endpoints (`/api/v1/approvals`, `/api/v1/budgets`, `/api/v1/policies`) and CLI commands (`varistha approvals`, `varistha policies`).
2. There was no web-based UI for an operator to inspect payloads, review unified JSON/text diffs, approve, reject, or edit and approve actions.
3. There was no visual circuit breaker board to monitor daily spends against caps or trigger emergency kill switches.

## Decision

### 1. Dedicated Governance Route (`/governance`)
Created `apps/ui/src/app/governance/page.tsx` adhering to the GitHub Primer design system:
- **Full-Width Header & Stats Bar**: Real-time KPI badges showing Global System Status (`Operational` vs `Emergency Stop`), Pending Approvals count, and Halted Agents count.
- **Sub-Navigation Tabs**: Clean tab switcher (`Human Approvals`, `Budgets & Circuit Breakers`, `Guardrails Explorer`) with amber counter pills.
- **Global Navbar Integration**: Added Governance navigation item in `apps/ui/src/components/navbar.tsx` featuring the `ShieldAlert` icon and a live dynamic pending approvals count.

### 2. Human Approvals Reviewer & Payload Diff Viewer
Built `apps/ui/src/components/governance/approvals-inbox.tsx` and `payload-diff-viewer.tsx`:
- **Status Filtering**: Filter pending, approved, rejected, edited, or all requests.
- **Interactive Inspection Modal**: Displays full agent metadata, proposed action type, tool name, justification/reasoning, and timestamp.
- **Unified Diff Engine**: Computes structured key-level additions, modifications, and deletions between original and edited parameters, rendering GitHub-style colored diff lines (`+` green, `-` red).
- **Three-Way Action Resolution**:
  - `Approve`: Resolves immediately with operator attribution.
  - `Reject`: Prompts for a mandatory rejection rationale before sending `POST /api/v1/approvals/{id}/resolve`.
  - `Edit & Approve`: Enables live JSON payload editing with syntax validation and instant diff computation prior to approval.

### 3. Budgets & Circuit Breakers Dashboard
Built `apps/ui/src/components/governance/budgets-dashboard.tsx`:
- **Platform Global Emergency Stop**: Prominent banner toggle with confirmation modal to halt or resume all agent operations instantly across the platform.
- **Agent Budget Cards & Progress Gauges**: Visual spend gauges showing daily spend vs budget caps, percentage utilization, remaining budget, and single-run spend ceilings (`max_usd_per_run`).
- **Circuit Breaker Controls**: One-click "Trip Kill Switch" (with required operational justification) and "Resume Agent" actions invoking the backend circuit breaker API.

### 4. Guardrails Explorer & Interactive Sandbox
Built `apps/ui/src/components/governance/guardrails-explorer.tsx`:
- **Policy Catalog**: Grid displaying active policies (`pii-redact`, `injection-scan`, `schema-valid`, `no-unverified-claims`), descriptions, and supported hooks (`input`, `output`, `tools`).
- **Interactive Testing Sandbox**: Live JSON/text payload tester executing `POST /api/v1/policies/test`, displaying evaluation status (`Passed` / `Blocked` / `Redacted`), action taken, violations list, and sanitized modified data.

## Consequences
- **Positive**: Operators have complete visual governance and human-in-the-loop oversight directly in the web UI.
- **Positive**: Strict adherence to the GitHub Primer design system (no hardcoded colors, semantic tokens, dark and light theme support).
- **Positive**: Fully covered by Vitest component unit tests (9 tests in `governance.test.tsx`, 32/32 UI tests passing) and zero TypeScript/ESLint warnings.
