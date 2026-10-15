# Plan: Phase 2, Task 3 — Lifecycle Board & Promotion UI

> **For Agent:** Implement Phase 2 Task 3 per `AGENTS.md` and `docs/SPEC.md § 3.2, § 4.4, § 5`.

**Goal:** Implement a responsive, high-fidelity Lifecycle Kanban Board in `apps/ui` with stage progression columns, live promotion gate verification checklists, an immutable stage audit history viewer, and a version spec diff modal.

---

## 1. Context & Motivation

Per `docs/SPEC.md § 5` (Phase 2 exit criteria):
- *"Registry UI shows lifecycle stage Kanban (draft, prototype, staging, production, deprecated, retired) with promotion actions."*
- *"An agent cannot be promoted without satisfying verifiable programmatic gates."*
- *"Show diffs, not blobs... A version change shows a spec diff."*

Operators need a visual control plane where AI agents are organized by their maturity stage. Promoting an agent must not be a mere toggle; it must present a live, interactive checklist of programmatic criteria (runs, owner, guardrails, evals, budget, kill switch) backed by the API endpoints developed in Task 1 & Task 2.

---

## 2. Design System & Accessibility Constraints (`docs/SPEC.md § 4.4`)

1. **Design Tokens & Colors:** Zero hardcoded hex colors (`check_boundaries.py`). Use Tailwind semantic tokens (`bg-background`, `text-foreground`, `border-border`, `text-muted-foreground`, etc.).
2. **Stage Badging:** Draft (grey), Prototype (blue), Staging (purple/violet), Production (green), Deprecated (amber), Retired (slate/zinc). Always paired with an icon.
3. **Responsive States:** Every component must have explicit loading skeletons, error banners with retry triggers, and empty states.
4. **Dense but Calm:** 14px base typography, generous whitespace, clean borders.

---

## 3. Data Structures & API Layer (`apps/ui/src/lib/`)

### Types (`types.ts`)
- `GateCheck`: `{ name: string; passed: boolean; message: string; }`
- `GateEvaluation`: `{ allowed: boolean; from_stage: string; to_stage: string; is_rollback: boolean; checks: GateCheck[]; error_message?: string | null; }`
- `StageTransition`: `{ id: string; agent_id: string; from_stage: string; to_stage: string; promoted_by: string; reason?: string | null; gate_results: Array<Record<string, unknown>>; created_at: string; }`
- `PromoteAgentRequest`: `{ to_stage: string; promoted_by: string; reason?: string | null; replacement?: string | null; kill_switch_verified?: boolean | null; secrets_revoked?: boolean | null; }`
- `PromoteAgentResponse`: `{ agent: AgentDetail; transition: StageTransition; evaluation: GateEvaluation; }`
- `DiffEntry`: `{ field: string; change_type: string; old_value?: unknown; new_value?: unknown; is_breaking: boolean; breaking_reason?: string | null; description: string; }`
- `SpecDiff`: `{ from_version?: string | null; to_version?: string | null; has_changes: boolean; has_breaking_changes: boolean; summary: Record<string, number>; entries: DiffEntry[]; breaking_entries: DiffEntry[]; }`

### API Methods (`api.ts`)
- `getGateEvaluation(idOrName, targetStage, options)`
- `promoteAgent(idOrName, payload)`
- `getStageHistory(idOrName)`
- `getVersionDiff(idOrName, v1, v2)`

---

## 4. Components Architecture (`apps/ui/src/components/`)

1. **`lifecycle-board.tsx`**:
   - 6 Kanban columns (`Draft`, `Prototype`, `Staging`, `Production`, `Deprecated`, `Retired`).
   - Column headers with StageBadge, item count, and stage definition summary.
   - Agent cards:
     - Name, version, owner email, primary model, autonomy badge.
     - Action buttons: "Promote" (opens PromoteModal), "History" (opens StageHistoryModal), "Diff" (opens VersionDiffModal).
   - Empty column states: "No agents in Staging", etc.

2. **`promote-modal.tsx`**:
   - Select target stage with forward canonical progression or rollback.
   - Real-time gate checklist fetched via `getGateEvaluation`.
   - Programmatic checklist items: green checkmark or red X badge, explanation.
   - Operator affirmation checkboxes:
     - Kill switch test verification (`kill_switch_verified`).
     - Secrets revocation confirmation (`secrets_revoked`).
     - Replacement slug input for deprecation.
     - Mandatory reason text for demotions/rollbacks.
   - "Confirm Promotion" disabled with warning when any gate fails.

3. **`stage-history-modal.tsx`**:
   - Timeline audit viewer of all historical stage transitions.
   - Shows operator, timestamp, stage progression, reason, and expandable gate outcomes.

4. **`version-diff-modal.tsx`**:
   - Version picker dropdowns (`v1` and `v2`).
   - Summary banner with change counts (+ added, - removed, ~ modified, ! breaking).
   - Prominent red alert if breaking changes are present.
   - Detailed field delta table.

5. **Navigation & Views (`apps/ui/src/app/`)**:
   - Add `/lifecycle` page.
   - Update `navbar.tsx` with "Lifecycle" link.
   - Provide view toggle ("Table" vs "Board") on `/agents`.

---

## 5. Verification & Testing

1. **Vitest Unit Tests**:
   - Test `LifecycleBoard` rendering, columns, and agent distribution.
   - Test `PromoteModal` gate checklist display and promotion submission.
   - Test `StageHistoryModal` audit log rendering.
   - Test `VersionDiffModal` diff display and breaking changes alert.
2. **Type Checking & Linting**:
   - `pnpm typecheck` (`tsc --noEmit`) passes with 0 errors.
   - `pnpm lint` (`eslint`) passes cleanly.
   - `python scripts/check_boundaries.py` (Rule 4: no hardcoded hex colors).
3. **Smoke Test with Live API**:
   - Verify Kanban board loads agents from the live dev SQLite database.
