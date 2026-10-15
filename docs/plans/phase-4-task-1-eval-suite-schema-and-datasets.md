# Implementation Plan: Phase 4 Task 1 — Eval Suite Schema, Dataset Models & DB Migration

## 1. Context & Objectives
Per `docs/SPEC.md § 4.2` (Core Data Model), `§ 5` (Phase 4: Evals and Confidence), and `AGENTS.md`:
- Varistha requires first-class evaluation suite specifications, dataset representations, and persistent storage for eval runs and granular results.
- Eval suites define test cases with inputs, expected outputs, criteria, and evaluator configurations (e.g. `contains`, `exact-match`, `regex`, `json-schema`, `semantic-similarity`, `llm-rubric`).
- Database models must track:
  1. `eval_suites`: Suite definition, target agent, configuration, file path.
  2. `eval_runs`: An execution of an eval suite against a specific agent version, recording overall `status`, `pass_rate`, `total_cases`, `passed_cases`, `failed_cases`, `duration_ms`, and `trigger`.
  3. `eval_results`: Granular per-test-case result with `input_data`, `expected_output`, `actual_output`, `passed`, `score`, `failure_reason`, and evaluator details.
- Database changes must be implemented exclusively via Alembic migration (`0005_evals.py`) supporting both SQLite (tests/dev) and PostgreSQL (production).

---

## 2. Architecture & Design

### 2.1 Eval Suite YAML Schema (`packages/spec/src/eval_models.py`)
```yaml
apiVersion: varistha/v1
kind: EvalSuite
metadata:
  name: lead-researcher-qualification
  agent: lead-researcher
  version: 1.0.0
spec:
  description: Tests qualification accuracy and ICP matching for incoming leads
  evaluators:
    - name: schema-check
      type: json-schema
    - name: contains-company
      type: contains
    - name: quality-judge
      type: llm-rubric
      model: gpt-class-or-any-litellm-id
  cases:
    - id: case-1
      name: Tech startup Series A
      input:
        company_name: Acme Cloud
        website: https://acmecloud.example.com
      expected:
        qualified: true
        tier: "Tier 1"
      evaluators:
        - schema-check
        - contains-company
```

### 2.2 Database Schema & Models (`apps/api/src/shared/db/models/eval.py`)
1. **`EvalSuite` (`eval_suites` table)**:
   - `id`: UUID (Primary Key)
   - `name`: String(100), not null, indexed
   - `agent_id`: UUID, foreign key to `agents.id`, cascade delete
   - `description`: Text, nullable
   - `config`: JSON / JSONB (evaluators, settings, metadata)
   - `created_at`: DateTime(timezone=True)
   - `updated_at`: DateTime(timezone=True)
   - Relationships: `agent`, `runs`

2. **`EvalRun` (`eval_runs` table)**:
   - `id`: UUID (Primary Key)
   - `suite_id`: UUID, foreign key to `eval_suites.id`, cascade delete
   - `agent_id`: UUID, foreign key to `agents.id`, cascade delete
   - `agent_version_id`: UUID, foreign key to `agent_versions.id`, nullable
   - `status`: String(30) (`pending`, `running`, `completed`, `failed`), default `pending`
   - `trigger`: String(30) (`manual`, `version_change`, `ci`, `schedule`)
   - `pass_rate`: Float (0.0 to 1.0), nullable
   - `total_cases`: Integer, default 0
   - `passed_cases`: Integer, default 0
   - `failed_cases`: Integer, default 0
   - `duration_ms`: Integer, nullable
   - `error_message`: Text, nullable
   - `created_at`: DateTime(timezone=True)
   - `completed_at`: DateTime(timezone=True), nullable
   - Relationships: `suite`, `agent`, `version`, `results`

3. **`EvalResult` (`eval_results` table)**:
   - `id`: UUID (Primary Key)
   - `eval_run_id`: UUID, foreign key to `eval_runs.id`, cascade delete, indexed
   - `case_id`: String(100), not null
   - `case_name`: String(255), not null
   - `input_data`: JSON / JSONB, not null
   - `expected_output`: JSON / JSONB, nullable
   - `actual_output`: JSON / JSONB, nullable
   - `passed`: Boolean, not null
   - `score`: Float, not null (0.0 to 1.0)
   - `evaluator_name`: String(100), not null
   - `evaluator_type`: String(50), not null
   - `failure_reason`: Text, nullable
   - `latency_ms`: Integer, nullable
   - `tokens_used`: Integer, nullable
   - `created_at`: DateTime(timezone=True)

### 2.3 Bounded Context Service & API (`apps/api/src/governance/evals/`)
- `schemas.py`:
  - `EvalSuiteCreate`, `EvalSuiteResponse`, `EvalSuiteListResponse`
  - `EvalRunCreate`, `EvalRunResponse`, `EvalRunListResponse`
  - `EvalResultResponse`, `EvalRunDetailResponse`
- `service.py`:
  - `create_or_update_suite(db, suite_data, agent_id)`
  - `get_suite(db, suite_id)`, `list_suites(db, agent_id=None)`
  - `create_eval_run(db, suite_id, agent_version_id, trigger)`
  - `record_eval_results(db, eval_run_id, results_list)`
  - `get_eval_run(db, run_id)`, `list_eval_runs(db, agent_id=None, suite_id=None)`
- `router.py`:
  - `POST /api/v1/evals/suites`: Register/update eval suite
  - `GET /api/v1/evals/suites`: List eval suites
  - `GET /api/v1/evals/suites/{id}`: Get suite details
  - `POST /api/v1/evals/runs`: Trigger / record an eval run
  - `GET /api/v1/evals/runs`: List eval runs
  - `GET /api/v1/evals/runs/{id}`: Get eval run details and granular results

---

## 3. Files to Touch

1. **`packages/spec/src/eval_models.py`**:
   - Pydantic models for declarative YAML eval suite format.
2. **`packages/spec/src/__init__.py`**:
   - Export eval models.
3. **`apps/api/src/shared/db/models/eval.py`**:
   - SQLAlchemy entities: `EvalSuite`, `EvalRun`, `EvalResult`.
4. **`apps/api/src/shared/db/models/__init__.py`**:
   - Export eval models.
5. **`apps/api/alembic/versions/0005_evals.py`**:
   - Alembic migration creating `eval_suites`, `eval_runs`, `eval_results`.
6. **`apps/api/src/governance/evals/schemas.py`**:
   - API request and response schemas.
7. **`apps/api/src/governance/evals/service.py`**:
   - CRUD and persistence business logic.
8. **`apps/api/src/governance/evals/router.py`**:
   - FastAPI endpoints under `/api/v1/evals`.
9. **`apps/api/src/governance/router.py`**:
   - Include `evals` router in governance routes.
10. **`apps/api/src/governance/tests/test_evals_models.py` & `test_evals_api.py`**:
    - Comprehensive unit and integration test coverage.

---

## 4. Verification & Testing Gate
1. `uv run pytest apps/api/src/governance/tests/test_evals*.py`
2. `uv run pytest apps/api/src/shared/tests/test_migrations.py`
3. `uv run ruff check .`
4. `uv run pyright`
5. `uv run bandit -r src -ll`
6. `git commit` and `git push`
7. Verify 100% green GitHub Actions.
