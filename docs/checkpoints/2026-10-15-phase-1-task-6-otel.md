# Milestone Checkpoint: Phase 1, Task 6 — OpenTelemetry Instrumentation & OTLP Receiver

- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 6 — OpenTelemetry instrumentation, OTLP receiver, and span persistence
- **Status**: PASSED
- **Timestamp**: 2026-10-15T15:10:00+05:30
- **Git Commit**: `4743325`
- **Reference Spec**: `docs/SPEC.md § 7.5 Task 6 & § 4.3`

---

## 1. Implemented Capabilities

1. **Shared Telemetry Kernel (`apps/api/src/shared/telemetry/`)**:
   - `conventions.py`: Semantic conventions for `varistha.*` (`VARISTHA_RUN_ID`, `VARISTHA_AGENT_ID`, `VARISTHA_AGENT_NAME`, `VARISTHA_AGENT_VERSION`, `VARISTHA_STAGE`, `VARISTHA_AUTONOMY`, `VARISTHA_COST_USD`, `VARISTHA_TRIGGER_TYPE`, etc.) and GenAI conventions (`GEN_AI_SYSTEM`, `GEN_AI_REQUEST_MODEL`, `GEN_AI_USAGE_TOTAL_TOKENS`, etc.).
   - `redaction.py`: PII and secret redaction engine sanitizing email addresses (`[REDACTED_EMAIL]`), Bearer tokens (`[REDACTED_TOKEN]`), and sensitive dictionary keys (`[REDACTED_SECRET]`) without colliding with token usage metrics (`*tokens`).
   - `setup.py`: OpenTelemetry TracerProvider initialization, service resource labeling, and span processor management.
   - `recorder.py`: In-process context-aware span recorder (`capture_run_spans(run_id)`), `RunSpanProcessor`, span-to-ORM model mapper (`span_to_db_model`), and persistence helper (`save_captured_spans`).

2. **Observability Bounded Context (`apps/api/src/observability/`)**:
   - `parser.py`: Robust OTLP JSON parser parsing `resourceSpans`, `scopeSpans`, and `spans`, unpacking protobuf `AnyValue` unions (string, int, double, bool, array, kvlist), converting nanosecond timestamps to UTC `datetime`, and mapping status codes.
   - `schemas.py`: Pydantic response models: `SpanResponse` (with computed `duration_ms`), `SpanListResponse`, `TraceDetailResponse`, and `OTLPExportResponse` (`partialSuccess`).
   - `service.py`: Database operations for querying spans by `run_id` and `trace_id`.
   - `router.py`: Endpoints for standard OTLP/HTTP JSON ingest (`POST /v1/traces`, `POST /api/v1/traces`) and span queries (`GET /api/v1/runs/{run_id}/spans`, `GET /api/v1/traces/{trace_id}`).

3. **Decoupled Runtime Tracing (`apps/api/src/runtime/`)**:
   - `service.py`: Wrapped `trigger_agent_run` in `capture_run_spans(run.id)` creating independent root span `agent.run` with `context=Context()` to isolate the run trace from HTTP server spans.
   - `adapter.py`: Wrapped `call_model_node` in `LangGraphRuntime` with `llm.call` child span recording model, tokens, and cost.
   - `mock.py`: Wrapped `MockRuntime.execute` with `llm.call` child span recording mock token usage and cost.

---

## 2. Test & Quality Metrics

- **Unit & Integration Tests Added**: 20 tests (6 telemetry kernel tests, 6 OTLP parser tests, 7 observability router tests, 1 runtime tracing integration test).
- **Cumulative Tests**: 126 passing tests across the monorepo.
- **Test Coverage**:
  - `apps/api/src/observability/`: 96% (`parser.py`: 98%, `router.py`: 96%, `schemas.py`: 100%, `service.py`: 89%).
  - `apps/api/src/shared/telemetry/`: 91% (`conventions.py`: 100%, `recorder.py`: 91%, `redaction.py`: 100%, `setup.py`: 83%).
  - Monorepo overall test coverage: 93% (exceeds ≥ 80% gate).
- **Linter Status**: `ruff check` clean (0 errors).
- **Format Status**: `ruff format --check` clean (0 errors).
- **Type Checker Status**: `pyright` strict clean (0 errors, 0 warnings).
- **Architecture Boundaries**: `check_boundaries.py` clean (0 cross-context violations, `runtime` does not import `observability`).
- **Architectural Decision Record**: `docs/adr/0007-opentelemetry-instrumentation-and-otlp-receiver.md`.

---

## 3. Artifact Manifest

- `apps/api/src/shared/telemetry/conventions.py`: OpenTelemetry semantic conventions.
- `apps/api/src/shared/telemetry/redaction.py`: PII and secret redaction utilities.
- `apps/api/src/shared/telemetry/setup.py`: OpenTelemetry TracerProvider configuration.
- `apps/api/src/shared/telemetry/recorder.py`: In-process span recorder and DB bridge.
- `apps/api/src/shared/telemetry/__init__.py`: Shared telemetry exports.
- `apps/api/src/shared/tests/test_telemetry.py`: Telemetry unit tests.
- `apps/api/src/observability/parser.py`: OTLP HTTP JSON payload parser.
- `apps/api/src/observability/schemas.py`: Observability Pydantic schemas.
- `apps/api/src/observability/service.py`: Span retrieval query services.
- `apps/api/src/observability/router.py`: OTLP ingest and span query endpoints.
- `apps/api/src/observability/tests/test_parser.py`: OTLP JSON parsing tests.
- `apps/api/src/observability/tests/test_router.py`: Observability API router tests.
- `apps/api/src/runtime/tests/test_tracing.py`: End-to-end runtime tracing integration test.
- `docs/plans/phase-1-task-6-otel.md`: Implementation plan.
- `docs/adr/0007-opentelemetry-instrumentation-and-otlp-receiver.md`: ADR 0007.
- `docs/checkpoints/2026-10-15-phase-1-task-6-otel.md`: Milestone checkpoint.

---

## 4. Known Gaps & Next Steps

- **Current State**: Phase 1 Tasks 1 through 6 are fully implemented and verified.
- **Next Task**: Phase 1, Task 7 — CLI commands `varistha init`, `varistha apply -f agent.yaml`, and `varistha run` in `packages/cli` (`docs/SPEC.md § 7.5 Task 7`).
