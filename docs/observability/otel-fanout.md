# OpenTelemetry Fan-Out & Observability Profiles

Varistha implements an open, standards-based observability architecture powered by the OpenTelemetry (OTel) standard and GenAI semantic conventions.

Rather than locking users into a heavy or proprietary AgentOps database, Varistha provides a dual-layer approach:
1. **Built-in Lightweight Observability**: A native, embedded trace store in PostgreSQL (`spans` table) accessible directly through the Control Plane API (`GET /api/v1/runs/{run_id}/spans`) and UI waterfall charts.
2. **Pluggable Fan-Out via OTel Collector**: An optional Docker Compose profile (`otel`) running `otel/opentelemetry-collector-contrib` that accepts OTLP traces and fans them out simultaneously to Varistha, Langfuse, Grafana Tempo, SigNoz, or Datadog.

---

## 1. Architecture

```
                 +--------------------------+
                 |  Varistha Agent Runtime  |
                 |  (LiteLLM + LangGraph)   |
                 +------------+-------------+
                              |
               OTel Traces (PII & Secrets Redacted)
                              |
           +------------------+------------------+
           |                                     |
   (Default Mode)                        (Profile: otel)
           |                                     |
+----------v-----------+              +----------v-----------+
| Direct DB Recording  |              |    OTel Collector    |
| (PostgreSQL `spans`) |              |  (Ports 4317 / 4318) |
+----------------------+              +----------+-----------+
                                                 |
                       +-------------------------+-------------------------+
                       |                         |                         |
            +----------v-----------+  +----------v-----------+  +----------v-----------+
            |  Varistha API        |  |  Langfuse            |  |  Grafana Tempo       |
            |  /v1/traces receiver |  |  (AgentOps UI)       |  |  (Distributed Traces)|
            +----------------------+  +----------------------+  +----------------------+
```

---

## 2. Default Setup vs. Observability Profile

To keep the initial developer ergonomics lightweight and adhere to the core rule of 4 containers on default `docker compose up` (`postgres`, `api`, `worker`, `ui`), the OTel Collector is isolated behind a Docker Compose profile:

### Default (Zero-Config)
```bash
docker compose up
```
- Only 4 containers started.
- All agent runs emit spans directly into the local PostgreSQL database.
- Traces are visible in the Varistha web UI at `/runs/[runId]/trace`.

### With OpenTelemetry Collector Fan-Out
```bash
docker compose --profile otel up
```
Or with overlay files:
```bash
docker compose -f docker-compose.yml -f docker-compose.otel.yml up
```
- Starts `varistha-otel-collector` on ports `4317` (gRPC) and `4318` (HTTP).
- Enables the `health_check` endpoint on port `13133`.
- Internal metrics available on port `8888`.

---

## 3. Configuration & External Backends

Configure the destinations in your `.env` file:

```env
# Point Varistha runtime to the Collector
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318/v1/traces
OTEL_SERVICE_NAME=varistha

# External Backend: Langfuse
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_AUTH_HEADER=Basic <base64(public_key:secret_key)>

# External Backend: Grafana Tempo
TEMPO_OTLP_ENDPOINT=tempo:4317
```

### Collector Configuration (`deploy/otel-collector-config.yaml`)

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  memory_limiter:
    check_interval: 1s
    limit_percentage: 75
    spike_limit_percentage: 20
  batch:
    send_batch_size: 256
    timeout: 1s

exporters:
  debug:
    verbosity: basic
  otlphttp/varistha:
    endpoint: ${VARISTHA_API_URL:-http://api:8000}/v1/traces
    tls:
      insecure: true
  otlphttp/langfuse:
    endpoint: ${LANGFUSE_HOST:-http://langfuse:3000}/api/public/otel/v1/traces
    headers:
      Authorization: Basic ${LANGFUSE_AUTH_HEADER:-}
  otlp/tempo:
    endpoint: ${TEMPO_OTLP_ENDPOINT:-tempo:4317}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [debug, otlphttp/varistha]
```

---

## 4. Telemetry Conventions & Security

All spans generated within Varistha strictly conform to:
1. **OpenTelemetry GenAI Conventions**:
   - `gen_ai.system`: Provider identifier (e.g. `litellm`, `openai`, `anthropic`).
   - `gen_ai.request.model`: Target LLM model name.
   - `gen_ai.usage.prompt_tokens`: Prompt token count.
   - `gen_ai.usage.completion_tokens`: Completion token count.
   - `gen_ai.usage.total_tokens`: Total token usage.
2. **Varistha Control Plane Conventions**:
   - `varistha.run_id`: Execution run UUID.
   - `varistha.agent_id`: Agent identifier.
   - `varistha.agent_name`: Agent slug.
   - `varistha.stage`: Current lifecycle stage (`draft`, `prototype`, `staging`, `production`).
   - `varistha.autonomy`: Autonomy tier (`L0`, `L1`, `L2`, `L3`).
   - `varistha.cost_usd`: Incremental cost calculation.
   - `varistha.approval_required`: Boolean flag indicating human approval pause.
   - `varistha.approval_status`: Human decision (`approved`, `rejected`, `edited`).

### Zero-Leakage & Redaction Guarantee
Before any span is passed to `SpanProcessor` or exported over OTLP:
- Inbound and outbound attribute values pass through `redact_attributes()` in `apps/api/src/shared/telemetry/redaction.py`.
- Detected PII (emails, phone numbers, SSNs, credit card numbers) is masked with standard placeholders (`[EMAIL_REDACTED]`).
- All API tokens, bearer keys, and secrets matching `sk-`, `ghp_`, `AKIA`, or authorization headers are stripped and masked with `[REDACTED_SECRET]`.
- Vault secrets stored in Postgres are never written to span attributes.
