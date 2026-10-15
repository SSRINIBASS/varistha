# Implementation Plan: Phase 1, Task 4 — Runtime Interface & LangGraph Adapter

## Task Information
- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 4 — Runtime interface and the first LangGraph adapter running a single-prompt agent through LiteLLM (`docs/SPEC.md § 7.5 Task 4`)
- **Estimated Scope**: ~400-500 lines across 8 files

---

## 1. Context & Objectives

The agent runtime executes an agent's workflow given an immutable spec snapshot and runtime inputs. Per `AGENTS.md` and `docs/SPEC.md`:
1. **Runtime Interface Isolation**: The core engine must not be tightly coupled to LangGraph. All runtime execution sits behind an abstract `Runtime` protocol (`apps/api/src/runtime/interface.py`).
2. **LangGraph Adapter**: Implements `Runtime` using LangGraph `StateGraph` in `apps/api/src/runtime/adapter.py`. **No LangGraph imports may exist outside `apps/api/src/runtime/`**.
3. **Model Access via LiteLLM**: All model calls must go through LiteLLM. **No direct provider SDKs (OpenAI, Anthropic, etc.) in core**.
4. **Offline & Mock Testing**: A `MockRuntime` (`apps/api/src/runtime/mock.py`) allows zero-cost, deterministic execution for integration tests and environments without API keys.
5. **API Surface**:
   - `POST /api/v1/agents/{id_or_name}/runs`: Trigger an agent run.
   - `GET /api/v1/agents/{id_or_name}/runs`: List runs for an agent.
   - `GET /api/v1/runs/{id}`: Retrieve run status, inputs, outputs, tokens, cost, and timestamps.

---

## 2. Component Design

### 2.1 Runtime Protocol & Data Contracts (`apps/api/src/runtime/interface.py`)
```python
@dataclass(frozen=True)
class RunContext:
    run_id: uuid.UUID
    agent_id: uuid.UUID
    agent_name: str
    model: str
    instructions: str
    input_data: dict[str, Any]
    spec_snapshot: dict[str, Any]


@dataclass(frozen=True)
class RunResult:
    status: str  # "completed" | "failed" | "waiting_approval"
    output: dict[str, Any]
    cost_usd: float
    total_tokens: int
    error: str | None = None


class Runtime(Protocol):
    async def execute(self, context: RunContext) -> RunResult: ...
```

### 2.2 LangGraph Adapter (`apps/api/src/runtime/adapter.py`)
- Defines agent state TypedDict: `AgentState(messages, input, output, tokens, cost)`.
- Builds a `StateGraph(AgentState)` compiled workflow.
- Invocation node invokes `litellm.acompletion()`.
- Computes token counts from `response.usage` and cost from `litellm.completion_cost()`.
- Gracefully handles exceptions and timeouts, mapping errors into `status="failed"`.

### 2.3 Mock Runtime (`apps/api/src/runtime/mock.py`)
- Deterministic response generator matching input payload or returning synthetic output.
- Emulates token consumption and simulated cost for tests and offline development.

### 2.4 Service Layer (`apps/api/src/runtime/service.py`)
- `create_and_start_run(session, agent_id_or_name, input_data, trigger_type, runtime)`:
  1. Resolves agent and retrieves current version spec.
  2. Creates `Run` record with status `running`, records `started_at`.
  3. Executes through `runtime.execute(context)`.
  4. Records `output`, `cost_usd`, `total_tokens`, `completed_at`, and final `status`.
- `get_run(session, run_id)` and `list_runs_for_agent(session, agent_id, limit, offset)`.

### 2.5 API Router (`apps/api/src/runtime/router.py`)
- Mounted under `/api/v1` with dependency injection for `Runtime`.

---

## 3. Files to Create / Modify

| File | Purpose |
| :--- | :--- |
| `apps/api/src/runtime/interface.py` | `Runtime` protocol, `RunContext`, `RunResult` dataclasses |
| `apps/api/src/runtime/adapter.py` | LangGraph `StateGraph` adapter using `litellm.acompletion` |
| `apps/api/src/runtime/mock.py` | `MockRuntime` for testing and offline environments |
| `apps/api/src/runtime/schemas.py` | Pydantic response/request models for runs |
| `apps/api/src/runtime/service.py` | Database persistence and execution orchestration |
| `apps/api/src/runtime/router.py` | FastAPI endpoints for triggering and retrieving runs |
| `apps/api/src/runtime/__init__.py` | Export public runtime components |
| `apps/api/src/main.py` | Mount `runtime_router` |
| `apps/api/src/runtime/tests/conftest.py` | Test fixtures for in-memory DB and runtime overrides |
| `apps/api/src/runtime/tests/test_interface.py` | Unit tests for Runtime contract & MockRuntime |
| `apps/api/src/runtime/tests/test_adapter.py` | Unit tests for LangGraph adapter with mocked litellm |
| `apps/api/src/runtime/tests/test_router.py` | Integration tests for run trigger and retrieval endpoints |

---

## 4. Verification & Quality Gates

1. **Unit & Integration Tests**:
   - `MockRuntime` execution success & failure modes.
   - `LangGraphRuntime` graph execution with mocked `litellm.acompletion`.
   - `POST /api/v1/agents/{id}/runs` creates pending -> completed run record.
   - `GET /api/v1/runs/{id}` returns correct status, tokens, output, and cost.
   - Run on non-existent agent returns 404.
   - Run on agent without published version returns 400.
2. **Acceptance Gates**:
   - Module test coverage ≥ 80% on `runtime/`.
   - `ruff check .` clean.
   - `ruff format --check .` clean.
   - `pyright apps/ packages/` strict clean.
   - `python scripts/check_boundaries.py` clean (verifies 0 LangGraph imports outside `runtime/` and 0 cross-context violations).
3. **Docs & Checkpoint**:
   - `docs/checkpoints/2026-10-15-phase-1-task-4-runtime.md`.
   - `docs/adr/0005-runtime-interface-and-langgraph-adapter.md`.
   - `CHANGELOG.md` entry.
