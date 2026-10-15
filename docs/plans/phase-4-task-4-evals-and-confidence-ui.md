# Implementation Plan: Phase 4 Task 4 — Evals & Confidence UI

## 1. Context & Objectives
Per `docs/SPEC.md § 4.4` (UI & Design System), `§ 5 (Phase 4)`:
- Operators need an interactive Evals UI:
  1. **Suite Runner**: Browse registered evaluation suites and execute an eval suite against an agent version with live feedback.
  2. **Test Case Results Explorer**: Inspect granular per-test-case assertions (pass/fail, score, evaluator type, latency ms, token cost, failure explanation).
  3. **Version Regression Comparator**: Compare base vs candidate evaluation runs side-by-side, displaying pass rate delta, latency delta, regressions, improvements, and per-case status.
  4. **Review-Priority / Confidence Sandbox**: View and evaluate verifiable multi-source confidence signals (schema validation, grounding citations, eval benchmarks, approval history) and review-priority level (`low`, `medium`, `high`, `critical`).
- Follow GitHub Primer design system: semantic CSS variable tokens (`bg-card`, `border-border`, `text-foreground`, etc.), light and dark theme compatibility, empty/loading/error states on all views.

---

## 2. Architecture & Design

### 2.1 Domain Types & API Client (`apps/ui/src/lib/types.ts` & `api.ts`)
- Add interfaces: `EvalSuite`, `EvalRun`, `EvalResult`, `EvalRunDetail`, `TestCaseComparison`, `EvalComparisonReport`, `ConfidenceSignal`, `ReviewPriorityOutcome`, `ConfidenceEvaluationRequest`.
- Add API functions: `getEvalSuites`, `getEvalSuite`, `createEvalSuite`, `executeEvalSuite`, `getEvalRuns`, `getEvalRun`, `compareEvalRuns`, `evaluateConfidence`.

### 2.2 Global Navigation Header (`apps/ui/src/components/navbar.tsx`)
- Add `Evals` navigation item (`href="/evals"`, icon `FlaskConical`, label `Evals`).

### 2.3 Evals UI Components (`apps/ui/src/components/evals/`)
- `eval-suite-runner.tsx`: Lists suites, executes suites with version selection and live progress, displays suite metadata.
- `eval-run-detail.tsx`: Displays execution metrics (pass rate, duration, cases) and granular test case assertions table with filter and inspector modal.
- `eval-regression-view.tsx`: Side-by-side version comparator with metric cards (delta, regressions, improvements) and assertion status table.
- `confidence-sandbox.tsx`: Interactive multi-signal review-priority calculator evaluating schema, grounding, benchmarks, and approval history.

### 2.4 Evals Page (`apps/ui/src/app/evals/page.tsx`)
- Top overview stats banner.
- UnderlineNav tab switcher: `Suites & Runner`, `Run History & Results`, `Version Comparison`, `Review Priority / Confidence`.
- Full loading, empty, and error states.

### 2.5 Tests (`apps/ui/src/__tests__/evals.test.tsx`)
- Unit and component tests for suite execution, assertion rendering, regression delta calculation, and review-priority badge display.

---

## 3. Verification Gate
1. `pnpm --dir apps/ui typecheck`
2. `pnpm --dir apps/ui test`
3. `uv run python scripts/check_boundaries.py` (checks for no hardcoded hex colors in UI)
4. Commit, push, and verify 100% green GitHub Actions.
