# ADR 0018: Offline Evaluation Execution Engine, Builtin Evaluator Library, and CLI

## Status
Accepted

## Context
Per `docs/SPEC.md § 3.1` (Autonomy Levels), `§ 4.1` (LiteLLM Model Gateway), and `§ 5` (Phase 4: Evals and Confidence):
1. Evaluating an agent's competence before deployment is a mandatory gate to autonomy.
2. In ADR 0017, we created the declarative YAML evaluation suite schema (`varistha/v1 EvalSuite`), database models (`eval_suites`, `eval_runs`, `eval_results`), and the foundational REST API.
3. However, there was no runtime engine capable of loading test cases, invoking the agent via LiteLLM or pluggable runners, executing deterministic and LLM-as-judge assertions, calculating aggregate pass rates, and recording granular metrics (score, latency, failure reason, tokens).
4. Developers and CI pipelines require both a REST API (`POST /api/v1/evals/suites/{id}/execute`) and a terminal command (`varistha eval run <suite_id_or_file>`) to run evaluations effortlessly.

## Decision

### 1. Evaluator Contracts and Library (`apps/api/src/governance/evals/evaluators/`)
Implemented an extensible evaluator framework:
- **`BaseEvaluator` & `EvaluatorOutcome`**: Standardized interface returning `passed: bool`, `score: float` (0.0 to 1.0), `failure_reason: str | None`, and `metadata: dict[str, Any]`.
- **`ExactMatchEvaluator`**: Checks strict equality or string whitespace-stripped equality.
- **`ContainsEvaluator`**: Validates substring presence, dictionary key-value matches, or list element containment.
- **`RegexEvaluator`**: Evaluates pattern matches using Python's `re` module with robust syntax error handling.
- **`JsonSchemaEvaluator`**: Validates structured dictionary or JSON string outputs against standard JSON schemas via `jsonschema`.
- **`GroundingEvaluator`**: Computes word-overlap citation and grounding ratio between actual output and input context.
- **`LLMRubricEvaluator`**: Invokes LiteLLM (`litellm.acompletion`) with custom scoring rubrics, parsing JSON score (0.0 to 1.0) and reasoning.
- **`create_evaluator` Factory**: Dynamically instantiates evaluators from declarative configuration dictionaries.

### 2. Eval Execution Engine (`apps/api/src/governance/evals/engine.py`)
Implemented `EvalExecutionEngine`:
- Accepts `db: AsyncSession`, `suite_id: UUID`, optional `agent_version_id: UUID`, and an optional custom `runner: Callable[[dict[str, Any]], Awaitable[Any]]`.
- Resolves target agent version and instructions from the database.
- Defaults to LiteLLM invocation using the agent's primary configured model and system prompt.
- Iterates over configured test cases, measuring latency and token usage.
- Executes applicable evaluators per case, recording all assertion outcomes into `eval_results`.
- Computes overall pass rate and persists finalized `EvalRun`.

### 3. REST API & CLI Command (`packages/cli/src/varistha_cli/commands/eval_cmd.py`)
- Mounted `POST /api/v1/evals/suites/{id}/execute` in `router.py`.
- Added CLI commands:
  - `varistha eval list [--agent <agent>] [--json]`: Lists registered suites.
  - `varistha eval run <suite_id_or_file> [--version <version>] [--json]`: Runs the suite, displaying a Rich summary panel and detailed assertions table. Exits with status code 1 if pass rate falls below 80%.

## Consequences
- **Positive**: Complete end-to-end evaluation pipeline from declarative YAML/DB spec to execution and granular assertion reporting.
- **Positive**: Strict architecture boundaries maintained — no cross-context imports between `governance`, `runtime`, and `registry`.
- **Positive**: CLI allows instant local evaluation before commits or CI pushes.
