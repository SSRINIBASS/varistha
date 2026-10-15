# ADR 0005: Runtime Interface & LangGraph Adapter Architecture

## Status
Accepted

## Context
Phase 1, Task 4 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 4`) requires establishing the agent runtime execution layer:
1. **Interface Isolation**: The agent framework ecosystem experiences rapid churn. The core control plane must not couple directly to LangGraph or any specific orchestrator.
2. **LangGraph Encapsulation**: LangGraph imports must remain strictly localized to `apps/api/src/runtime/` as mandated by architecture boundaries (`scripts/check_boundaries.py`).
3. **Model Provider Decoupling**: All LLM interactions must go through LiteLLM. No provider SDKs (OpenAI, Anthropic) may be imported in core.
4. **Deterministic Testing**: Integration and API test suites must run in CI/local environments without requiring live LLM API keys or incurring dollar costs.

## Decision

### 1. Abstract `Runtime` Protocol (`apps/api/src/runtime/interface.py`)
We defined an asynchronous `@runtime_checkable Protocol`:
```python
class Runtime(Protocol):
    async def execute(self, context: RunContext) -> RunResult: ...
```
- `RunContext`: Immutable dataclass containing `run_id`, `agent_id`, `agent_name`, `model`, `instructions`, `input_data`, and `spec_snapshot`.
- `RunResult`: Immutable dataclass containing `status` (`completed`, `failed`, `waiting_approval`), `output`, `cost_usd`, `total_tokens`, and optional `error`.

### 2. LangGraph Runtime Adapter (`apps/api/src/runtime/adapter.py`)
- Implements `Runtime` by compiling a `StateGraph(AgentState)` single-prompt workflow.
- Node execution invokes `litellm.acompletion(model, messages, timeout)`.
- Calculates total token usage from `response.usage` and estimates dollar cost via `litellm.completion_cost(completion_response=response)`.
- Parses JSON structured responses automatically while gracefully falling back to wrapped raw strings.
- Captures API exceptions and maps them to `RunResult(status="failed", error=...)`.

### 3. Mock Runtime (`apps/api/src/runtime/mock.py`)
- Provides a fast, deterministic, zero-cost `MockRuntime` for development, unit, and API integration testing.
- Allows test-controlled failure injection, custom token/cost counts, and approval-waiting states.

### 4. Service & Endpoint Architecture
- `apps/api/src/runtime/service.py`: Orchestrates agent resolution, active version spec lookup, `Run` record persistence (`status="running"` -> `status="completed" | "failed"`), token tracking, and duration timestamps.
- `apps/api/src/runtime/router.py`:
  - `POST /api/v1/agents/{id_or_name}/runs`: Trigger agent run.
  - `GET /api/v1/agents/{id_or_name}/runs`: List runs for agent.
  - `GET /api/v1/runs/{id}`: Retrieve run status, input/output, cost, and tokens.
- Injected via FastAPI dependency `get_runtime()`, allowing seamless test override.

## Consequences

### Positive
- Strict isolation: swapping LangGraph in the future only requires writing a new `Runtime` adapter class.
- Automated tests run 100% offline with zero external network dependency or LLM costs.
- Zero boundary violations: 0 LangGraph imports outside `runtime/`, 0 provider SDKs in core, and 0 cross-context dependencies.

### Negative / Trade-offs
- Single-prompt graph is simple; multi-step tool-calling graphs will require expanding the graph topology in Task 5 (MCP plugins).
