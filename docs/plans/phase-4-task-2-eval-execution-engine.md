# Implementation Plan: Phase 4 Task 2 — Offline Eval Execution Engine & Evaluator Library

## 1. Context & Objectives
Per `docs/SPEC.md § 3.1` (Autonomy Levels), `§ 4.1` (LiteLLM Model Gateway), and `§ 5` (Phase 4: Evals and Confidence):
- An agent cannot be promoted or trusted without offline evaluation on version changes.
- Varistha needs an offline eval execution engine that tests agents against datasets, runs deterministic and LLM-as-judge evaluators, records granular test case assertions, and computes an overall pass rate.
- Evaluators must include:
  1. `exact-match`: Strict value equality.
  2. `contains`: Substring or key/value presence.
  3. `regex`: Pattern matching.
  4. `json-schema`: Structural output validation.
  5. `grounding`: Citation/grounding ratio against input context.
  6. `llm-rubric`: LLM-as-judge evaluation through LiteLLM.
- The engine must be executable via API (`POST /api/v1/evals/suites/{id}/execute`) and CLI (`varistha eval run`).

---

## 2. Architecture & Design

### 2.1 Pluggable Evaluators (`apps/api/src/governance/evals/evaluators/`)
- `interface.py`:
  - `EvaluatorOutcome`: `passed: bool`, `score: float` (0.0 to 1.0), `failure_reason: str | None`, `metadata: dict[str, Any]`
  - `BaseEvaluator`: Abstract base class with async `evaluate(output: Any, expected: Any, context: dict[str, Any]) -> EvaluatorOutcome`
- Builtin Evaluators:
  - `ExactMatchEvaluator`: Checks `output == expected` or json equality.
  - `ContainsEvaluator`: Checks if expected substring / key / items exist within output.
  - `RegexEvaluator`: Checks `re.search(pattern, str(output))`.
  - `JsonSchemaEvaluator`: Validates dictionary or parsed JSON output against schema.
  - `GroundingEvaluator`: Calculates overlap/grounding ratio between extracted claims and source input.
  - `LLMRubricEvaluator`: Asks LiteLLM judge model to score output (0.0 to 1.0) and output reasoning.

### 2.2 Execution Engine (`apps/api/src/governance/evals/engine.py`)
- `EvalExecutionEngine`:
  - Input: `db: AsyncSession`, `suite: EvalSuite`, `agent_version_id: uuid.UUID | None = None`, `runtime: Runtime | None = None`.
  - Workflow:
    1. Look up agent spec for the target version.
    2. Instantiate target runtime (LangGraph adapter or Mock).
    3. Iterate over test cases defined in `suite.config["cases"]`:
       - Measure execution latency and invoke agent with `case.input`.
       - Run matching evaluators against agent output.
       - Synthesize case score and pass/fail flag.
    4. Persist run and granular test case assertions via `record_eval_results`.
    5. Return finalized `EvalRun`.

### 2.3 API & CLI
- Endpoint: `POST /api/v1/evals/suites/{id}/execute?version_id=...`
- CLI: `varistha eval run <suite_id_or_file> [--version <ver>]` with Rich output table and pass/fail summary badge.

---

## 3. Files to Touch
1. `apps/api/src/governance/evals/evaluators/interface.py`: Evaluator contracts.
2. `apps/api/src/governance/evals/evaluators/builtin.py`: Builtin evaluators.
3. `apps/api/src/governance/evals/evaluators/__init__.py`: Registry and factory.
4. `apps/api/src/governance/evals/engine.py`: `EvalExecutionEngine`.
5. `apps/api/src/governance/evals/router.py`: `POST /suites/{id}/execute`.
6. `packages/cli/src/varistha_cli/commands/eval_cmd.py`: CLI command `varistha eval`.
7. `packages/cli/src/varistha_cli/main.py`: Register `eval` command group.
8. `apps/api/src/governance/tests/test_eval_engine.py`: Unit and integration tests.
9. `packages/cli/tests/test_eval_cmd.py`: CLI tests.

---

## 4. Verification & Testing Gate
1. `uv run pytest apps/api/src/governance/tests/test_eval_engine.py`
2. `uv run pytest packages/cli/tests/test_eval_cmd.py`
3. `uv run ruff check .`
4. `uv run pyright`
5. `git commit` and `git push`
6. Verify 100% green GitHub Actions.
