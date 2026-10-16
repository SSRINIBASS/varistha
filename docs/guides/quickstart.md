# 5-Minute Quickstart Guide

Get Varistha up and running, deploy your first AI employee, trigger an execution, review a human-in-the-loop approval, and view the OpenTelemetry trace waterfall in under five minutes.

---

## 1. Prerequisites

Before starting, ensure you have installed:
- **Docker** and **Docker Compose v2+**
- **Git**
- *(Optional for CLI)* **Python 3.12+** or **uv**

---

## 2. Launch Control Plane Services

Varistha includes a zero-dependency Docker Compose configuration bringing up PostgreSQL 16 (with pgvector), the FastAPI Core API, the Worker Engine, and the Next.js Dashboard:

```bash
# Clone the repository
git clone https://github.com/SSRINIBASS/varistha.git
cd varistha

# Copy the default environment configuration
cp deploy/.env.example deploy/.env

# Start all core containers in detached mode
docker compose -f deploy/docker-compose.yml up -d
```

Verify that all services are healthy:
```bash
docker compose -f deploy/docker-compose.yml ps
```

You can now open:
- **Control Plane UI**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/healthz](http://localhost:8000/healthz)

---

## 3. Install the Varistha CLI

Install the CLI using `pip` or `uv`:

```bash
# Using pip
pip install varistha-cli

# Or install from local repository
pip install -e packages/cli
```

Verify the installation:
```bash
varistha --version
# Output: varistha, version 0.1.0
```

---

## 4. Initialize an Agent Specification

Create a new declarative agent specification file:

```bash
varistha init --name b2b-researcher --role "Find B2B prospects and draft outreach"
```

This generates `agent.yaml`:

```yaml
apiVersion: varistha/v1
kind: Agent
metadata:
  name: b2b-researcher
  owner: founder@example.com
  stage: prototype
  version: 0.1.0
spec:
  role: Find B2B prospects and draft outreach
  model:
    primary: gpt-4o-mini
    fallback: gpt-3.5-turbo
  instructions: |
    Analyze company domain and extract key executives and offerings.
    Draft a personalized outreach email.
  plugins:
    - name: web-fetch
      enabled: true
    - name: email-draft
      enabled: true
  autonomy: L1
  guardrails:
    input:
      - pii-redact
      - injection-scan
    output:
      - schema-valid
    tools:
      - outbound-needs-approval
  budget:
    max_usd_per_run: 0.50
    max_usd_per_day: 10.00
  triggers:
    - type: manual
```

---

## 5. Register and Execute the Agent

Apply the specification to your local control plane:

```bash
varistha apply -f agent.yaml
```

Trigger an execution run with an input payload:

```bash
varistha run b2b-researcher --input '{"domain": "stripe.com"}'
```

The CLI outputs the created Run ID and current status (`waiting_approval`).

---

## 6. Review Approval & Trace in UI

1. Open [http://localhost:3000/approvals](http://localhost:3000/approvals) in your browser.
2. You will see a pending approval item created by `b2b-researcher` for the outbound action `email-draft`.
3. Click the item to inspect the proposed email draft side-by-side with an interactive editor.
4. Click **Approve** (or use keyboard shortcut `a`).

Alternatively, approve directly from the CLI:
```bash
varistha approvals list
varistha approvals approve <approval-id>
```

Open [http://localhost:3000/runs](http://localhost:3000/runs) to inspect the complete execution trace:
- Model latency, prompt tokens, and completion tokens.
- Guardrail checks (`pii-redact` and `injection-scan`).
- Tool execution timings and inputs/outputs.
- Approval wait duration.

---

## Next Steps

- Explore [Core Concepts & Lifecycle Stages](concepts.md)
- Learn how to use prebuilt [Role Packs](role-packs.md)
- Learn how to author custom [MCP Plugins](plugin-authoring.md)
- Read the [Production Hardening Guide](production-hardening.md)
