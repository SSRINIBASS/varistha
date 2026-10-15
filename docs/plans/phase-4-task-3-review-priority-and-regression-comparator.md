# Implementation Plan: Phase 4 Task 3 — Review-Priority Engine, Version Regression Comparator & Promotion Gate Wiring

## 1. Context & Objectives
Per `docs/SPEC.md § 2 (Critique item 7)` and `§ 5 (Phase 4)`:
- Model-reported confidence is uncalibrated; confidence must be derived from verifiable signals (schema validation, grounding, eval benchmarks, approval history).
- Evals must support version-over-version regression comparison: detecting which test cases regressed, which improved, and overall pass-rate delta.
- Evaluation run outcomes must be wired into lifecycle promotion gates: promotion from `prototype` to `staging` and `staging` to `production` must be blocked if evaluations have not been run or if the pass rate falls below the required threshold.

---

## 2. Architecture & Design

### 2.1 Verifiable Review-Priority / Confidence Engine (`apps/api/src/governance/confidence/`)
- `engine.py` / `schemas.py`:
  - `ConfidenceSignal`: `name: str`, `weight: float`, `score: float`, `passed: bool`, `details: str`
  - `ReviewPriorityOutcome`:
    - `confidence_score`: float (0.0 to 1.0)
    - `review_priority`: Literal["low", "medium", "high", "critical"]
    - `signals`: list[ConfidenceSignal]
    - `rationale`: str
  - Signals:
    1. `schema_validation`: Checks if output parses and adheres to expected schema. (Weight: 0.25)
    2. `grounding_citation`: Measures input/source context keyword and citation coverage. (Weight: 0.25)
    3. `eval_benchmark`: Uses latest completed offline eval suite pass rate for the agent version. (Weight: 0.25)
    4. `approval_history`: Historical human approval rate for this agent's past runs. (Weight: 0.25)
  - Endpoint: `POST /api/v1/governance/confidence/evaluate`

### 2.2 Version Regression Comparator (`apps/api/src/governance/evals/comparator.py`)
- `compare_eval_runs(base_run: EvalRun, candidate_run: EvalRun) -> EvalComparisonReport`:
  - `base_version`: str
  - `candidate_version`: str
  - `base_pass_rate`: float
  - `candidate_pass_rate`: float
  - `pass_rate_delta`: float (e.g. +0.10 or -0.05)
  - `status`: Literal["improved", "regressed", "unchanged"]
  - `regressions`: list of test cases that passed in base but failed in candidate
  - `improvements`: list of test cases that failed in base but passed in candidate
  - `latency_delta_ms`: int
- Endpoint: `GET /api/v1/evals/compare`

### 2.3 Wiring Evals into Lifecycle Promotion Gates
- In `apps/api/src/registry/gates.py`:
  - Accept `eval_runs: list[dict[str, Any]] | None` in `evaluate_stage_transition_gates`.
  - In `prototype -> staging`:
    - Gate `eval_suite_passed`: Checks that at least one completed eval run exists on this version and its `pass_rate >= min_pass_rate` (default 0.8).
  - In `staging -> production`:
    - Gate `eval_score_threshold`: Checks that the current version's eval run meets the threshold.
- In `apps/api/src/registry/service.py`:
  - Fetch latest `EvalRun` for the version from `shared.db.models.eval.EvalRun` and supply to `evaluate_stage_transition_gates`.

---

## 3. Files to Touch
1. `apps/api/src/governance/confidence/schemas.py`: Confidence and review-priority models.
2. `apps/api/src/governance/confidence/engine.py`: Verifiable confidence signal evaluator.
3. `apps/api/src/governance/confidence/router.py`: REST endpoint for confidence evaluation.
4. `apps/api/src/governance/evals/comparator.py`: Version regression comparator service.
5. `apps/api/src/governance/evals/router.py`: Endpoint `GET /api/v1/evals/compare`.
6. `apps/api/src/registry/gates.py`: Wire real eval run pass rate into promotion gates.
7. `apps/api/src/registry/service.py`: Query latest eval run and pass to gate evaluation.
8. `apps/api/src/governance/tests/test_confidence.py`: Unit and API tests for confidence engine.
9. `apps/api/src/governance/tests/test_comparator.py`: Unit tests for regression comparison.
10. `apps/api/src/registry/tests/test_gates.py`: Update and add tests verifying eval gate blocking.
11. `docs/adr/0019-review-priority-and-regression-comparator.md`: Architecture decision record.
12. `CHANGELOG.md`: Record Phase 4 Task 3 updates.

---

## 4. Verification Gate
1. `uv run python scripts/check_boundaries.py`
2. `uv run ruff check .` and `uv run ruff format --check .`
3. `uv run pyright`
4. `uv run pytest` (coverage &ge; 80%)
5. Git commit, push, and verify 100% green GitHub Actions.
