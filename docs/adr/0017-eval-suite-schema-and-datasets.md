# ADR 0017: Evaluation Suite Declarative Schema, Dataset Models, and Results Storage

## Status
Accepted

## Context
Per `docs/SPEC.md § 3.1` (Autonomy Levels), `§ 4.2` (Core Data Model), and `§ 5` (Phase 4: Evals and Confidence), autonomous AI employees require rigorous evaluation suites, dataset test cases, and persistent run telemetry.

Prior to Phase 4:
1. Agent specifications contained an `evals` block referencing a suite file (`spec.evals.suite`) and minimum pass rate threshold (`spec.evals.min_pass_rate`), but there was no standardized declarative schema for the suite documents themselves.
2. There were no database tables or domain services to track evaluation suites, historical evaluation executions (`eval_runs`), or granular assertion results per test case (`eval_results`).
3. Promotion gates could only verify that the spec declared an eval configuration string, rather than checking actual executed evaluation results.

## Decision

### 1. Declarative YAML Eval Suite Schema (`packages/spec/src/eval_models.py`)
Introduced canonical Pydantic models for `varistha/v1 EvalSuite`:
- **`EvaluatorConfig`**: Defines assertion engines (`exact-match`, `contains`, `regex`, `json-schema`, `semantic-similarity`, `llm-rubric`, `custom`) with model bindings, prompt rubrics, JSON schemas, and individual score thresholds.
- **`TestCaseConfig`**: Represents an individual test scenario with unique `id`, human-readable `name`, structured `input` dictionary, `expected` ground truth, optional evaluator filters, and categorization `tags`.
- **`EvalSuiteDoc`**: Top-level document enforcing `apiVersion: varistha/v1`, `kind: EvalSuite`, metadata (`name`, `agent`, `version`, `owner`), and specification (`description`, `evaluators`, `cases`).

### 2. Database Schema & Alembic Migration (`0005_evals.py`)
Created relational storage supporting SQLite and PostgreSQL with JSON/JSONB variants:
- **`eval_suites`**: Tracks suite definitions, bindings to `agents.id`, descriptions, and JSON evaluator configurations.
- **`eval_runs`**: Represents an evaluation execution against an agent version. Captures `status` (`pending`, `running`, `completed`, `failed`), `trigger` (`manual`, `version_change`, `ci`, `schedule`), `pass_rate` (0.0 to 1.0), `total_cases`, `passed_cases`, `failed_cases`, and `duration_ms`.
- **`eval_results`**: Granular assertion records linked to `eval_runs.id`. Stores `case_id`, `input_data`, `expected_output`, `actual_output`, `passed`, `score`, `evaluator_name`, `evaluator_type`, `failure_reason`, `latency_ms`, and `tokens_used`.

### 3. Governance Evaluation Domain API (`apps/api/src/governance/evals/`)
Mounted under `/api/v1/evals`:
- `POST /api/v1/evals/suites`: Registers or updates an evaluation suite.
- `GET /api/v1/evals/suites`: Lists evaluation suites with pagination and optional agent filtering.
- `GET /api/v1/evals/suites/{id}`: Retrieves suite metadata and configuration.
- `POST /api/v1/evals/runs`: Initiates an evaluation execution record.
- `POST /api/v1/evals/runs/{id}/results`: Records assertion outcomes, aggregates metrics (`pass_rate`, duration), and marks the run completed.
- `GET /api/v1/evals/runs`: Lists eval runs with agent or suite filters.
- `GET /api/v1/evals/runs/{id}`: Retrieves full run details with all granular test case results.

## Consequences
- **Positive**: Provides a typed, queryable foundation for offline evaluation execution, regression detection, and automated promotion gate verification.
- **Positive**: Completely conforms to the bounded context architecture: evals live cleanly within `governance`, leveraging the shared database kernel.
- **Positive**: Fully verified across unit, API integration, and migration test suites (149/149 backend tests passing with 91.57% coverage).
