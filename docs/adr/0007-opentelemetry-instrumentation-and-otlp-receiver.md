# ADR 0007: OpenTelemetry Instrumentation and OTLP Receiver Architecture

## Status
Accepted

## Context
Phase 1, Task 6 of the Varistha roadmap (`docs/SPEC.md § 7.5 Task 6` & `§ 4.3`) requires end-to-end observability across the control plane:
1. **OpenTelemetry Semantic Conventions**: Every agent run, LLM call, tool call, guardrail check, and human approval wait must emit spans conforming to GenAI semantic conventions and the `varistha.*` namespace.
2. **OTLP/HTTP Receiver**: External workers, sandboxes, and runtimes should be able to send spans directly to Varistha over standard OpenTelemetry HTTP JSON protocol (`POST /v1/traces` and `POST /api/v1/traces`).
3. **Database Persistence**: Spans must be stored directly in the `spans` table for queryability, waterfall visualization, and cost attribution.
4. **Clean Bounded Context Boundaries**: `runtime/` and `observability/` must remain completely decoupled. Per `AGENTS.md`, cross-context imports are strictly forbidden.
5. **PII and Secret Redaction**: Secrets, tokens, and PII must be redacted before export or persistence without corrupting numeric telemetry metrics (e.g. token counts).
6. **Root Trace Isolation**: Spec § 4.3 mandates "One trace per run". When an agent run is triggered via an HTTP endpoint, it must not be subordinated as a child span of the incoming HTTP request.

## Decision

### 1. Shared Telemetry Kernel (`apps/api/src/shared/telemetry/`)
To satisfy the strict boundary check (`scripts/check_boundaries.py`), telemetry primitives and span recording reside in the shared kernel:
- **`conventions.py`**: Defines standard attributes:
  - `varistha.run_id`, `varistha.agent_id`, `varistha.agent_name`, `varistha.agent_version`
  - `varistha.stage`, `varistha.autonomy`, `varistha.cost_usd`, `varistha.trigger_type`
  - GenAI conventions: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.prompt_tokens`, `gen_ai.usage.completion_tokens`, `gen_ai.usage.total_tokens`
- **`redaction.py`**: Masks PII (emails, auth tokens, secrets, API keys) while explicitly avoiding collisions with token metrics (`*tokens`).
- **`setup.py`**: Configures the OpenTelemetry `TracerProvider` with `Resource` attributes (`service.name=varistha-api`).
- **`recorder.py`**: Provides `capture_run_spans(run_id)` context manager and `RunSpanProcessor` that intercepts spans in-process, converts them to DB `Span` ORM instances via `span_to_db_model()`, and persists them upon run completion via `save_captured_spans()`.

### 2. Observability Bounded Context (`apps/api/src/observability/`)
- **`parser.py`**: Decodes standard OTLP/HTTP JSON payloads (`resourceSpans`), unpacking protobuf `AnyValue` fields (string, int, double, bool, array, kvlist) into native Python dictionaries, converting nanosecond UNIX timestamps to UTC `datetime`, and extracting `varistha.run_id`.
- **`schemas.py`**: Strict Pydantic models for span queries (`SpanResponse`, `TraceDetailResponse`) with computed fields (`duration_ms`) and OTLP export response with `partialSuccess` alias.
- **`service.py`**: Handles DB queries for spans by `run_id` and `trace_id`.
- **`router.py`**: Exposes:
  - `POST /v1/traces` & `POST /api/v1/traces`: Standard OTLP JSON ingest endpoints.
  - `GET /api/v1/runs/{run_id}/spans`: Retrieve all spans for an agent execution run.
  - `GET /api/v1/traces/{trace_id}`: Retrieve all spans for a specific distributed trace.

### 3. Decoupled Runtime Tracing
- When `trigger_agent_run` is invoked in `runtime/service.py`, it executes inside `capture_run_spans(run.id)` and starts root span `agent.run` passing `context=Context()` explicitly to isolate the trace from incoming HTTP request spans.
- Runtime nodes in `adapter.py` and `mock.py` wrap model executions with `llm.call` child spans emitting model attributes, token counts, and computed USD costs.

## Consequences

### Positive
- Strict compliance with OpenTelemetry standards allows drop-in integration with both standard OTLP collectors and in-process tracing.
- No cross-context imports between `runtime` and `observability` — zero architectural violations.
- Spans are persisted immediately to Postgres / SQLite, enabling rich waterfall views in the UI.
- PII and secrets are scrubbed before persistence.
- High test coverage: 93% across observability and shared telemetry modules.

### Negative / Trade-offs
- OTLP JSON parsing currently handles standard dictionary payloads. High-volume deployments in later phases may benefit from binary protobuf decoding or streaming ingestion to a dedicated collector.
