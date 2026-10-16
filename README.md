# Varistha

<div align="center">

**Open-source, self-hostable control plane to build, run, monitor and govern AI agents (AI employees) for startups.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-GenAI%20Spans-F5A800.svg?logo=opentelemetry&logoColor=white)](https://opentelemetry.io)
[![Test Coverage](https://img.shields.io/badge/Coverage-97%25-brightgreen.svg)](https://github.com/SSRINIBASS/varistha)

[Quickstart](#quick-start) • [Architecture](#architecture) • [Core Capabilities](#core-capabilities) • [Role Packs](#role-packs) • [Documentation](docs/) • [Contributing](CONTRIBUTING.md)

</div>

---

## Why Varistha?

Most AI agents built today operate like scripts running in the dark:
- No central registry of who owns which agent or what version is running.
- No guardrails preventing hallucinated or sensitive outbound actions (emails, social posts, CRM updates).
- No spending controls stopping runaway loops from burning API budgets.
- Fragmented logs with zero visibility into model latency, token economics, or tool inputs/outputs.

**Varistha is the operational foundation for autonomous AI employees.** It gives engineering and ops teams a unified control plane with stage promotion gates, human-in-the-loop approvals, pluggable MCP tools, OpenTelemetry fan-out, and multi-user RBAC.

---

## Architecture

```
                       +-------------------+
                       |    Next.js UI     |
                       | (shadcn / Radix)  |
                       +---------+---------+
                                 |
                                 v
                       +-------------------+
                       |   FastAPI Core    |
                       |  (Control Plane)  |
                       +----+----+----+----+
                            |    |    |
       +--------------------+    |    +--------------------+
       |                         v                         |
+------v--------+       +-----------------+       +--------v-------+
|  PostgreSQL   |       |  Worker Engine  |       | OTel Collector |
|   16 with     |       | (LangGraph RT / |       |  (Prometheus,  |
|   pgvector    |       |  LiteLLM Gate)  |       |   Langfuse)    |
+---------------+       +---+---------+---+       +----------------+
                            |         |
                  +---------v--+   +--v----------+
                  |  LiteLLM   |   | MCP Plugins |
                  |  Gateway   |   | (Fetch, CRM,|
                  | (Any Model)|   |  Email, Web)|
                  +------------+   +-------------+
```

### Core Architecture Invariants
- **Runtime Abstraction**: LangGraph engine isolated behind a strict `Runtime` protocol (`apps/api/src/runtime/`).
- **Model Gateway**: All inference routed through LiteLLM. No vendor SDK imports in core.
- **MCP Extensibility**: All agent tools are sandboxed Model Context Protocol plugins.
- **Outside-the-Model Security**: Guardrails, budgets, and approval locks are enforced in deterministic application code, never delegated to model prompts.
- **Pure OTel Instrumentation**: Standard GenAI semantic conventions with `varistha.*` domain attributes.

---

## Core Capabilities

### 1. Build
- **Declarative YAML Specs**: Define agents as code with versioning, model selection, fallback models, MCP plugins, autonomy levels (L0 to L4), and triggers.
- **Ready-to-Use Role Packs**: Install pre-packaged AI employees with curated prompts, eval datasets, and tools (e.g. Lead Researcher, Competitor Intelligence, Outbound SDR).
- **Extensible MCP Ecosystem**: Out-of-the-box support for Web Search, Scrape (Crawl4AI & Playwright), Email Draft & Send, LinkedIn, X, and CRM exports.

### 2. Run
- **Durable Execution Engine**: LangGraph checkpointing with persistent run state and interrupt capabilities.
- **Multi-Trigger Dispatch**: Trigger runs manually, via cron schedules, or through authenticated webhook endpoints.
- **Budgetary Enforcement**: Hard token and currency limits per-run and per-day with a global emergency kill switch.
- **Concurrently Scalable**: Certified for high concurrency (10+ parallel agents stable).

### 3. Govern (AgentOps)
- **Human-in-the-Loop Inbox**: Review, edit, approve, or reject outbound actions before execution with side-by-side diff views.
- **Automated Guardrails**: Input/output PII redaction, prompt injection scanning, schema validation, and rate limiting.
- **Eval Engine & Regression Gates**: Automated benchmark suites (accuracy, hallucination detection, format compliance) gating promotion between stages.
- **Enterprise Security & Auth**: Multi-user RBAC (`admin`, `operator`, `viewer`), AES-256-GCM encrypted secrets vault at rest, and SSRF-hardened networking.

---

## Quick Start

### 1. Start with Docker Compose

Varistha runs out of the box with zero external SaaS dependencies:

```bash
# Clone repository
git clone https://github.com/SSRINIBASS/varistha.git
cd varistha

# Copy environment variables
cp deploy/.env.example deploy/.env

# Start all core services (Postgres, API, Worker, UI)
docker compose -f deploy/docker-compose.yml up -d
```

Open your browser to:
- **Dashboard UI**: [http://localhost:3000](http://localhost:3000)
- **REST API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/healthz](http://localhost:8000/healthz)

### 2. Optional Observability Profile

To fan out OpenTelemetry traces to an OTel Collector, Langfuse, or Grafana Tempo:

```bash
docker compose -f deploy/docker-compose.yml --profile otel up -d
```

---

## CLI Usage

Install the Varistha CLI to manage agent specs and runs directly from your terminal:

```bash
# Install via pip
pip install varistha-cli

# Initialize a new agent spec from template
varistha init --name lead-researcher --role "B2B Lead Enrichment"

# Validate and apply spec to control plane
varistha apply -f agent.yaml

# Trigger execution and follow trace stream
varistha run lead-researcher --input '{"company": "acme-corp.com"}'

# Review pending human approvals
varistha approvals list
varistha approvals approve <approval-id>
```

---

## Role Packs

Varistha comes bundled with operational role packs located in `role-packs/`:

| Role Pack | Description | Autonomy | Default Tools |
|---|---|---|---|
| **Lead Research** | Discovers B2B leads, extracts executives, technologies, and drafts outreach. | L1 | `web-search`, `web-scrape`, `email-draft` |
| **Competitor Intel** | Monitors competitor websites, pricing pages, and product launches. | L2 | `web-scrape`, `web-search`, `crm-export` |
| **Outbound SDR** | Personalizes outbound prospect communication subject to human review. | L1 | `email-draft`, `email-send`, `crm-export` |
| **Support Responder**| Triages incoming tickets and drafts verified response recommendations. | L1 | `email-draft`, `crm-export` |
| **Content Repurposer**| Analyzes articles/docs and creates social posts for X and LinkedIn. | L2 | `web-fetch`, `linkedin-post`, `x-post` |

---

## Documentation

- **[5-Minute Quickstart](docs/guides/quickstart.md)**
- **[Core Concepts & Lifecycle Stages](docs/guides/concepts.md)**
- **[Agent Spec Guide](docs/guides/agent-spec-guide.md)**
- **[Role Packs Guide](docs/guides/role-packs.md)**
- **[Plugin Authoring Guide](docs/guides/plugin-authoring.md)**
- **[Backup & Restore Runbook](docs/runbooks/backup-and-restore.md)**
- **[Threat Model & Production Checklist](docs/security/threat-model.md)**
- **[OTel Fan-Out & Observability](docs/observability/otel-fanout.md)**

---

## Security

Security is treated as a hard system requirement:
- Web and user inputs are strictly classified as **untrusted data**.
- All secrets are encrypted at rest using **AES-256-GCM** with HKDF key derivation.
- Fetch and scrape plugins enforce strict SSRF blocks against private and link-local IP addresses.
- Outbound actions require human approval at Autonomy L1 and below.

To report security vulnerabilities, review [SECURITY.md](SECURITY.md) or email **security@varistha.dev**.

---

## License

Varistha is open-source software licensed under the [Apache License, Version 2.0](LICENSE).
All core dependencies and built-in plugins adhere to OSI-approved open-source licensing.
