# Plan: Phase 3, Task 4 — Governance UI Dashboard & Approvals Reviewer

## Context & Objectives
Per `docs/SPEC.md § 3.3, § 4.4, § 5`:
Varistha requires an operator-grade Governance UI dashboard following GitHub Primer design aesthetics (full-span layout, GitHub cards, octicon-style badges, Coral/Blue/Green/Red accenting, dark/light mode responsive, zero hardcoded colors).

The Governance UI completes the operator experience for Phase 3:
1. **Approvals Inbox**: Displays pending approvals with count badges, tool/action context, proposed payloads, approved payloads, side-by-side JSON diffing, and one-click actions (`Approve`, `Reject`, `Edit`).
2. **Budgets & Kill Switches**: Displays daily spend vs limit progress bars, per-run caps, individual agent kill/resume controls, and a platform-wide Global Emergency Stop control banner.
3. **Guardrails Explorer & Playground**: Active policy catalog showing supported hook points (`input`, `output`, `tools`) and an interactive sandbox to test policies against arbitrary inputs.

## Components & File Plan

### 1. API Client Extensions (`apps/ui/src/lib/api.ts`)
- TypeScript types:
  - `ApprovalItem`, `ApprovalsListResponse`, `ApprovalResolveRequest`
  - `AgentBudgetStatus`, `GlobalKillSwitchStatus`
  - `PolicyInfo`, `PolicyListResponse`, `PolicyTestRequest`, `PolicyTestResponse`
- Client methods:
  - `getApprovals(params?: { status?: string, agentId?: string, runId?: string })`
  - `getApproval(id: string)`
  - `resolveApproval(id: string, action: string, modifiedPayload?: Record<string, unknown>, rationale?: string)`
  - `getAgentBudget(idOrName: string)`
  - `tripAgentKillSwitch(idOrName: string, reason: string, operator?: string)`
  - `resumeAgent(idOrName: string, operator?: string)`
  - `getGlobalKillSwitch()`
  - `setGlobalKillSwitch(enabled: boolean, reason?: string, operator?: string)`
  - `getPolicies()`
  - `testPolicy(policyName: string, payload: unknown, hook?: string)`

### 2. Navigation Update (`apps/ui/src/components/navbar.tsx`)
- Add `Governance` tab to global UnderlineNav with `ShieldAlert` icon and pending approval count pill.

### 3. Governance Components (`apps/ui/src/components/governance/`)
- `approvals-inbox.tsx`:
  - Filter tabs: `Pending`, `Approved`, `Rejected`, `Edited`, `All`.
  - Cards / rows displaying agent name, action type, tool name, timestamp, and status badge.
  - Interactive approval drawer / modal:
    - Side-by-side payload viewer.
    - JSON diff preview highlighting modifications.
    - Inline JSON editor for `edit` action.
    - Approve / Reject buttons with confirmation and rationale input.
- `budgets-dashboard.tsx`:
  - Global Emergency Stop warning banner with toggle modal.
  - Agent budget cards showing:
    - Daily spend vs `max_usd_per_day` progress bar.
    - `max_usd_per_run` cap.
    - Kill switch badge (`ACTIVE` vs `HALTED`).
    - Action buttons: "Trip Kill Switch" (modal with reason prompt) and "Resume Agent".
- `guardrails-explorer.tsx`:
  - Active policies table with description and hook pills (`input`, `output`, `tools`).
  - Interactive test sandbox: select policy, input text/JSON, execute test, view color-coded result panel with violations and redacted payload.
- `payload-diff-viewer.tsx`:
  - GitHub Primer styled unified/split JSON diff viewer.

### 4. Page View (`apps/ui/src/app/governance/page.tsx`)
- Full-span container with sub-navigation tabs:
  - "Approvals"
  - "Budgets & Circuit Breakers"
  - "Guardrails & Policies"
- Live metrics row: Pending Approvals count, Tripped Kill Switches, Total Daily Spend, Registered Policies.

### 5. Vitest Tests (`apps/ui/tests/governance.test.tsx`)
- Unit tests verifying:
  - API client methods for approvals, budgets, and policies.
  - Component rendering for approvals list, empty states, and status badges.
  - Payload diff calculations and formatting.

## Verification & Acceptance Gates
1. `pnpm --dir apps/ui run lint` passes with 0 errors.
2. `pnpm --dir apps/ui run test` passes with 0 failures.
3. `pnpm --dir apps/ui run build` completes production bundle successfully.
4. Browser validation: visual verification with dark/light mode toggle.
5. Git commit & push with CI / Code Review monitoring.
