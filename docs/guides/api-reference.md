# Varistha REST API Reference

The Varistha Control Plane exposes a versioned REST API at `/api/v1`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## 1. System Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/healthz` | Liveness and database connectivity health probe. | No |
| `GET` | `/metrics` | Prometheus metrics scrape endpoint. | No |

---

## 2. Registry Context (`/api/v1/agents`)

Manage declarative agent specifications, version snapshots, and lifecycle stage transitions.

| Method | Endpoint | Description | Minimum Role |
|---|---|---|---|
| `GET` | `/api/v1/agents` | List registered agents (supports `stage` and `owner` filters). | `viewer` |
| `POST` | `/api/v1/agents` | Register a new agent from an Agent Spec YAML payload. | `operator` |
| `GET` | `/api/v1/agents/{id}` | Retrieve agent details, current version, and stage. | `viewer` |
| `PUT` | `/api/v1/agents/{id}` | Update agent metadata or active specification. | `operator` |
| `GET` | `/api/v1/agents/{id}/versions` | List historical immutable version snapshots. | `viewer` |
| `POST` | `/api/v1/agents/{id}/stage` | Transition agent to a new lifecycle stage (eval gates checked). | `operator` |
| `POST` | `/api/v1/agents/{id}/diff` | Compare two versions or preview changes against remote spec. | `viewer` |

---

## 3. Runtime Context (`/api/v1/agents/{id}/runs`)

Execute agents, stream events, inspect execution status, and query OpenTelemetry traces.

| Method | Endpoint | Description | Minimum Role |
|---|---|---|---|
| `POST` | `/api/v1/agents/{id}/runs` | Trigger a new execution run with input JSON payload. | `operator` |
| `GET` | `/api/v1/runs` | List execution runs across all agents with status filters. | `viewer` |
| `GET` | `/api/v1/runs/{id}` | Retrieve run status (`pending`, `running`, `waiting_approval`, `completed`, `failed`). | `viewer` |
| `GET` | `/api/v1/traces/{trace_id}` | Retrieve complete OTel span hierarchy and waterfall data for a run. | `viewer` |

---

## 4. Governance Context (`/api/v1/approvals` & `/policies`)

Human-in-the-loop review, automated guardrail policies, eval suites, and budgets.

| Method | Endpoint | Description | Minimum Role |
|---|---|---|---|
| `GET` | `/api/v1/approvals` | List pending and historical human approval requests. | `viewer` |
| `POST` | `/api/v1/approvals/{id}/decision` | Approve, edit-and-approve, or reject a pending outbound action. | `operator` |
| `GET` | `/api/v1/policies` | List active guardrail policies (PII redaction, injection scan, rate limits). | `viewer` |
| `POST` | `/api/v1/policies` | Register or update a guardrail policy. | `admin` |
| `GET` | `/api/v1/budgets/{agent_id}` | Inspect current spend and rolling daily budget status. | `viewer` |
| `POST` | `/api/v1/budgets/{agent_id}/kill` | Trip circuit-breaker kill switch for an agent. | `operator` |
| `POST` | `/api/v1/budgets/emergency-stop` | Toggle global emergency stop halting all agents across control plane. | `admin` |
| `POST` | `/api/v1/evals/runs` | Trigger offline evaluation suite execution. | `operator` |
| `GET` | `/api/v1/evals/results/{id}` | Inspect evaluation scores and regression comparison. | `viewer` |

---

## 5. Identity & Auth Context (`/api/v1/auth`)

Multi-user role-based access control, API keys, and encrypted secrets vault.

| Method | Endpoint | Description | Minimum Role |
|---|---|---|---|
| `GET` | `/api/v1/auth/me` | Inspect current authenticated identity and permissions. | `viewer` |
| `GET` | `/api/v1/auth/keys` | List active API keys (metadata only). | `admin` |
| `POST` | `/api/v1/auth/keys` | Generate a new API key with a designated role (`admin`, `operator`, `viewer`). | `admin` |
| `DELETE` | `/api/v1/auth/keys/{id}` | Revoke an API key. | `admin` |
| `GET` | `/api/v1/auth/secrets` | List secret names and descriptions in the encrypted vault. | `operator` |
| `POST` | `/api/v1/auth/secrets` | Store a secret (encrypted at rest via AES-256-GCM). | `admin` |
| `GET` | `/api/v1/auth/secrets/{name}` | Resolve and decrypt a secret value. | `admin` |
| `DELETE` | `/api/v1/auth/secrets/{name}` | Delete a secret from the vault. | `admin` |

---

## 6. Plugins Context (`/api/v1/plugins`)

Discover installed Model Context Protocol (MCP) capabilities.

| Method | Endpoint | Description | Minimum Role |
|---|---|---|---|
| `GET` | `/api/v1/plugins` | List all discovered MCP plugins, tool catalogs, and risk tiers. | `viewer` |
| `GET` | `/api/v1/plugins/{name}` | Retrieve plugin manifest, exposed tools, and configuration schema. | `viewer` |
