# Implementation Plan: Phase 6 Task 4 - OpenTelemetry Fan-Out & Observability Profiles

## Objective
Implement OpenTelemetry fan-out and observability profiles in Varistha as mandated by `docs/SPEC.md § 2 (Critique 2 & 3)`, `§ 4 (Architecture)`, and `§ 5 (Phase 6)`.

The default stack remains strictly 4 lightweight containers (`postgres`, `api`, `worker`, `ui`) on `docker compose up`. By enabling the `otel` profile (`docker compose --profile otel up`), an OpenTelemetry Collector container starts, receiving standard OTLP traces (gRPC on port 4317, HTTP on port 4318) and fanning them out to:
1. **Varistha Control Plane**: `http://api:8000/v1/traces` (persisting into local Postgres `spans` table for built-in UI inspection).
2. **Langfuse**: OTLP HTTP export to Langfuse (`${LANGFUSE_HOST}/api/public/otel/v1/traces`) with basic auth header from public/secret keys.
3. **Grafana Tempo / SigNoz**: OTLP gRPC export to `${TEMPO_OTLP_ENDPOINT}`.
4. **Debug**: Console logging of span metadata for rapid local debugging.

Additionally, update Varistha's telemetry initialization in `apps/api/src/shared/telemetry/setup.py` so that if `OTEL_EXPORTER_OTLP_ENDPOINT` is set in the environment, a batch OTLP HTTP span exporter is automatically registered.

---

## Files to Touch & Create

1. **`deploy/otel-collector-config.yaml`** (New)
   - OpenTelemetry Collector Contrib configuration.
   - Receivers: OTLP gRPC (`0.0.0.0:4317`) and HTTP (`0.0.0.0:4318`).
   - Processors: `memory_limiter`, `batch`.
   - Exporters: `otlphttp/varistha`, `debug`, `otlphttp/langfuse`, `otlp/tempo`.
   - Pipelines: Traces pipeline routing through processors to configured exporters.
   - Extensions: `health_check` on port 13133.

2. **`deploy/docker-compose.yml`** (Update)
   - Add `otel-collector` service with `profiles: ["otel"]`.
   - Mounts `./otel-collector-config.yaml`.
   - Exposes ports 4317, 4318, 8888, 13133.
   - Depends on `api: service_healthy`.

3. **`deploy/docker-compose.otel.yml`** (New)
   - Docker Compose overlay file providing standalone override syntax:
     `docker compose -f docker-compose.yml -f docker-compose.otel.yml up`.

4. **`deploy/.env.example`** (Update)
   - Add OTel collector & fan-out environment variables with detailed descriptions:
     `OTEL_EXPORTER_OTLP_ENDPOINT`, `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `TEMPO_OTLP_ENDPOINT`.

5. **`apps/api/pyproject.toml`** (Update)
   - Include `opentelemetry-exporter-otlp-proto-http>=1.28.0` (Apache-2.0, CNCF/PyCA audited).

6. **`apps/api/src/shared/telemetry/setup.py`** (Update)
   - Add support for `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable in `init_tracer_provider()`.
   - Attach `BatchSpanProcessor(OTLPSpanExporter(endpoint=...))` when configured.
   - Graceful fallback on missing dependencies or invalid endpoints.

7. **`docs/observability/otel-fanout.md`** (New)
   - Documentation for setting up external observability backends (Langfuse, Grafana Tempo, SigNoz).
   - Trace flow diagrams and security/redaction guarantees.

8. **Tests**:
   - `apps/api/src/shared/tests/test_otel_collector_config.py` (New):
     - Validates YAML syntax and schema of `otel-collector-config.yaml`.
     - Validates Compose profile definition in `docker-compose.yml` and `docker-compose.otel.yml`.
   - `apps/api/src/shared/tests/test_telemetry_export.py` (New):
     - Unit tests for `setup.py` OTLP exporter attachment, endpoint resolution, and graceful failure.

---

## Verification & Acceptance Criteria
- [x] Zero extra containers in default `docker compose up` (4 containers preserved).
- [x] `docker compose --profile otel up` loads the OTel collector.
- [x] Collector configuration validates cleanly with standard OTLP receivers and multi-exporter fan-out.
- [x] Setting `OTEL_EXPORTER_OTLP_ENDPOINT` attaches batch exporter in `setup.py`.
- [x] All 7 core security invariants preserved (PII and secrets redacted before spans leave the process).
- [x] All automated checks pass: `ruff`, `pyright`, `python scripts/check_boundaries.py`, `pip-audit`, `pytest`.
