# ADR 0019: Review-Priority Confidence Engine, Version Regression Comparator, and Promotion Gate Wiring

## Status
Accepted

## Context
Per `docs/SPEC.md § 2 (Critique item 7)`, `§ 3.2` (Lifecycle Stages and Promotion Gates), and `§ 5` (Phase 4: Evals and Confidence):
1. **Model-reported confidence is uncalibrated**: LLM self-reported confidence numbers cannot be trusted for automated decision making or risk assessment. Confidence must be derived from verifiable multi-source signals: structural schema conformity, input source grounding/citations, offline evaluation suite pass rate, and historical human operator approval rates.
2. **Evals must detect regressions**: Changing agent instructions, model versions, or prompts often improves some scenarios while breaking others. Operators need a regression comparator to detect which specific test cases regressed, which improved, latency deltas, and net pass-rate changes.
3. **Evals must gate promotions**: Per `docs/SPEC.md § 3.2`, promotion from `prototype` to `staging` and `staging` to `production` must be strictly blocked if offline evaluations have not been run or if the pass rate falls below the required threshold.

## Decision

### 1. Verifiable Review-Priority / Confidence Engine (`apps/api/src/governance/confidence/`)
- Implemented `ReviewPriorityEngine` calculating review priority (`low`, `medium`, `high`, `critical`) and an aggregate confidence score (0.0 to 1.0) derived from four verifiable signals (weight 0.25 each):
  1. `schema_validation`: Validates candidate output against standard JSON schema via `jsonschema`.
  2. `grounding_citation`: Measures keyword and citation overlap ratio between candidate output and input source context.
  3. `eval_benchmark`: Inspects the latest completed offline evaluation run for the agent version.
  4. `approval_history`: Queries historical human operator approval rate (approved vs rejected/edited) for this agent.
- Added endpoint `POST /api/v1/governance/confidence/evaluate`.

### 2. Version Regression Comparator (`apps/api/src/governance/evals/comparator.py`)
- Implemented `compare_eval_runs(base_run: EvalRun, candidate_run: EvalRun) -> EvalComparisonReport`:
  - Compares test case assertions side-by-side.
  - Categorizes test cases as `regressed`, `improved`, `unchanged`, `added`, or `removed`.
  - Computes `pass_rate_delta`, `latency_delta_ms`, `regressions_count`, and `improvements_count`.
  - Determines net verdict: `improved`, `regressed`, or `unchanged`.
- Added endpoint `GET /api/v1/evals/compare?base_run_id=...&candidate_run_id=...`.

### 3. Wiring Eval Runs into Promotion Gates (`apps/api/src/registry/`)
- In `apps/api/src/registry/gates.py`:
  - Extended `evaluate_stage_transition` to accept `eval_runs: list[dict[str, Any]] | None = None`.
  - `prototype -> staging`: Added gate check `eval_suite_passed`, ensuring at least one completed evaluation run exists with `pass_rate >= min_pass_rate` (default 0.80).
  - `staging -> production`: Enforced `eval_score_threshold` against real completed `EvalRun` records.
  - Maintained backward compatibility for tests without `eval_runs` by falling back to spec evaluation configuration presence.
- In `apps/api/src/registry/service.py`:
  - `evaluate_gates_for_agent` queries completed `EvalRun` records directly from `shared.db.models.eval` and passes them to `evaluate_stage_transition`.
  - Strict bounded context isolation is preserved without cross-context imports between `registry` and `governance`.

## Consequences
- **Positive**: Operators and control planes have a principled, verifiable confidence mechanism rather than self-reported LLM confidence.
- **Positive**: Regressions between agent versions are immediately visible per test case with deltas in pass rate and latency.
- **Positive**: Lifecycle transitions strictly prevent unverified or failing agents from advancing to staging or production.
- **Positive**: Zero architectural boundary violations (`scripts/check_boundaries.py` clean).
