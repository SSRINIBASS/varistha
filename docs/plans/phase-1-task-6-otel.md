# Implementation Plan: Phase 1, Task 6 — OpenTelemetry Instrumentation & OTLP Receiver

## 1. Goal & Context
- **SPEC Reference**: `docs/SPEC.md § 7.5 Task 6`, `§ 4.3 Telemetry conventions`, `§ 4 Architecture`.
- **Goal**: Implement OpenTelemetry tracing across agent runs and LLM calls, provide a standard OTLP/HTTP receiver (`POST /v1/traces`) in the FastAPI control plane, persist spans into the PostgreSQL/SQLite `spans` table with `varistha.*` semantic conventions, and expose query endpoints for traces and run span waterfalls.

---

## 2. Architecture & Design Principles

### Bounded Context Boundaries
- `apps/api/src/observability`: Bounded context handling OTLP ingestion, span storage, and trace querying. It imports only `shared/` kernel and external libraries (`fastapi`, `pydantic`, `sqlalchemy`). Zero imports of `runtime/`, `registry/`, or `governance/`.
- `apps/api/src/shared/telemetry`: Shared telemetry kernel providing OpenTelemetry tracer configuration, `varistha.*` semantic conventions, and PII/secret redaction. Accessible by all contexts.
- `apps/api/src/runtime`: Emits spans via standard `opentelemetry.trace` API and `shared.telemetry` conventions. Zero direct imports of `observability/`.

### OTLP Standard Compliance
- Receives standard OTLP HTTP/JSON trace exports (`application/json`) at `POST /v1/traces` and `POST /api/v1/traces`.
- Decodes OTLP `ExportTraceServiceRequest` payload containing `resourceSpans`, `scopeSpans`, and `spans`.
- Handles standard OTel attributes (unwrapping `stringValue`, `intValue`, `doubleValue`, `boolValue`, `arrayValue`, `kvlistValue` or raw values).
- Converts nano timestamps (`startTimeUnixNano`, `endTimeUnixNano`) to timezone-aware UTC `datetime`.
- Extracts `run_id` from attributes (`varistha.run_id`), resource attributes, query params (`?run_id=...`), or header (`X-Varistha-Run-Id`).

### Security & Privacy Rules (Treat as Hard Requirements)
- **Zero Secret Leakage**: Redact sensitive keys (`password`, `secret`, `token`, `api_key`, `authorization`) before persisting or exporting spans.
- **PII Redaction**: Email and credit-card regex masking on attribute strings.

---

## 3. Files to Create and Modify

| Path | Purpose |
|------|---------|
| `apps/api/src/shared/telemetry/__init__.py` | Package export for shared telemetry utilities. |
| `apps/api/src/shared/telemetry/conventions.py` | Constants for `varistha.*` and GenAI semantic conventions. |
| `apps/api/src/shared/telemetry/redaction.py` | Redacts secrets and PII from span attributes and events. |
| `apps/api/src/shared/telemetry/setup.py` | Tracer provider setup and custom span exporter / processor. |
| `apps/api/src/observability/__init__.py` | Package export for observability context. |
| `apps/api/src/observability/schemas.py` | Pydantic response models: `SpanResponse`, `SpanListResponse`, `TraceDetailResponse`. |
| `apps/api/src/observability/parser.py` | Parser for OTLP JSON requests into database `Span` attributes. |
| `apps/api/src/observability/service.py` | Service functions: `ingest_otlp_traces`, `get_spans_by_run_id`, `get_trace`. |
| `apps/api/src/observability/router.py` | FastAPI endpoints: `POST /v1/traces`, `POST /api/v1/traces`, `GET /api/v1/runs/{id}/spans`, `GET /api/v1/traces/{trace_id}`. |
| `apps/api/src/main.py` | Mount `observability_router`. |
| `apps/api/src/runtime/service.py` | Add span creation for agent run execution. |
| `apps/api/src/runtime/adapter.py` | Add child span creation for `llm.call` with token usage and cost. |

---

## 4. Test Strategy (TDD)

1. `apps/api/src/shared/tests/test_telemetry.py`:
   - Test secret redaction (`authorization`, `api_key`, `password`).
   - Test PII masking (email addresses in attributes).
   - Test semantic conventions constants.
2. `apps/api/src/observability/tests/test_parser.py`:
   - Test parsing standard OTLP JSON export with various AnyValue types.
   - Test nano timestamp conversion to UTC datetime.
   - Test fallback to root run_id from resource or attributes.
3. `apps/api/src/observability/tests/test_router.py`:
   - Integration test: `POST /v1/traces` ingesting valid OTLP payload and persisting to database.
   - Integration test: `GET /api/v1/runs/{id}/spans` returning ordered waterfall spans.
   - Integration test: `GET /api/v1/traces/{trace_id}` returning all spans for a trace.
   - Error cases: Unknown run ID, invalid payload, malformed timestamps.
4. `apps/api/src/runtime/tests/test_tracing.py`:
   - Integration test verifying that invoking `trigger_agent_run` emits trace spans with GenAI attributes and `varistha.run_id`.

---

## 5. Verification Commands
- `uv run pytest` (all existing + new tests passing, ≥ 80% coverage on new modules)
- `uv run ruff check . && uv run ruff format --check .`
- `uv run pyright`
- `python scripts/check_boundaries.py`
