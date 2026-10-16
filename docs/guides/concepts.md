# Core Concepts & Architecture

Varistha is designed around a single guiding philosophy: **AI agents running in businesses should be governed with the same engineering discipline as human employees and software microservices.**

---

## 1. The Three Pillars

```
+-------------------------------------------------------------+
|                          VARISTHA                           |
+-------------------+--------------------+--------------------+
|     1. BUILD      |      2. RUN        |     3. GOVERN      |
+-------------------+--------------------+--------------------+
| - Agent Spec YAML | - LangGraph Runtime| - Human Approvals  |
| - Version History | - Multi-Trigger    | - Policy Engine    |
| - Role Packs      | - LiteLLM Gateway  | - Budgets & Kill   |
| - MCP Plugins     | - State Checkpoint | - OTel GenAI Trace |
+-------------------+--------------------+--------------------+
```

1. **Build**: Define declarative, versioned specifications (`agent.yaml`) that define models, instructions, plugins, autonomy levels, and guardrails.
2. **Run**: Execute agents reliably through a durable, checkpointed runtime engine with flexible triggers (manual, schedule, webhook) and multi-model fallbacks.
3. **Govern (AgentOps)**: Guarantee safety with policy gates, human-in-the-loop approvals for outbound writes, token budget limits, and comprehensive OpenTelemetry tracing.

---

## 2. Lifecycle Stages & Promotion Gates

Every agent progresses through formal lifecycle stages tracked in an immutable audit ledger:

| Stage | Badge Color | Description | Promotion Gate Requirements |
|---|---|---|---|
| **Draft** | Slate / Gray | Spec authoring and experimental iteration. | None. |
| **Prototype** | Blue | Functional sandbox testing on development data. | Valid schema, owner email assigned. |
| **Staging** | Violet | Pre-production testing against eval test suites. | Eval pass rate &ge; threshold (e.g. 85%), no active regressions. |
| **Production** | Green | Live execution servicing business workflows. | Formal promotion approval, security checklist satisfied, budget configured. |
| **Deprecated** | Amber | Scheduled for phaseout; no new runs accepted. | Administrative action with migration notes. |
| **Retired** | Red | Inactive and archived; kept for historical audit. | Terminal state. |

### Promotion Gates
Stage transitions are enforced in code outside the model. If an agent spec does not meet the criteria for Staging or Production, promotion is rejected with an explicit typed error.

---

## 3. Autonomy Levels (L0 to L4)

Varistha categorizes agent autonomy into five explicit levels:

- **L0 (Manual / Copilot)**: The model suggests steps, but every single action must be triggered and approved by a human.
- **L1 (Action Approval - Default)**: The agent executes read-only steps autonomously (e.g. web search, scraping, database queries). Any **outbound or side-effecting action** (email send, social post, CRM write) automatically pauses execution and creates an Approval Request.
- **L2 (Supervised)**: Outbound actions execute autonomously within pre-approved parameter ranges; actions exceeding thresholds trigger approval.
- **L3 (Monitored)**: Full autonomy during normal operations; anomalies or safety guardrail violations trigger an immediate interrupt.
- **L4 (Autonomous)**: Full autonomy with retrospective auditing and budget caps.

---

## 4. Human-in-the-Loop Approvals

When an agent at Autonomy L1 or below attempts an outbound action:
1. The execution engine suspends execution and persists the state checkpoint.
2. An `Approval` record is created with:
   - Run ID and Agent ID
   - Action name (e.g., `email-send`)
   - Proposed payload (e.g., recipient, subject, body)
3. The human reviewer can:
   - **Approve**: Resumes execution with proposed output.
   - **Edit & Approve**: Modifies proposed text (e.g. editing an outreach email); the system stores both original and edited diffs for model fine-tuning and eval datasets.
   - **Reject**: Cancels action and aborts run with feedback.

---

## 5. Policy Engine & Guardrails

Guardrails run in deterministic Python middleware before and after model inference and tool execution:

- **Input Guardrails**:
  - `pii-redact`: Masks credit card numbers, Social Security numbers, email addresses, and phone numbers before sending to the model.
  - `injection-scan`: Scans input strings for indirect prompt injection and system instruction override patterns.
- **Output Guardrails**:
  - `schema-valid`: Validates model structured output against a strict Pydantic/JSON Schema.
  - `no-unverified-claims`: Verifies claims against source retrieval chunks.
- **Tool Guardrails**:
  - `outbound-needs-approval`: Flags side-effecting tool calls.
  - `rate-limit`: Restricts maximum tool invocations per run or per hour.

---

## 6. Budgetary Controls & Circuit Breakers

To protect startups from runaway agent loops and unexpected API bills:
- **`max_usd_per_run`**: Maximum cost permitted for a single execution run (e.g. $0.50). If exceeded, the run is immediately aborted.
- **`max_usd_per_day`**: Rolling 24-hour spending limit across all runs for an agent (e.g. $10.00). If exceeded, future runs are blocked.
- **Global Emergency Stop (`emergency-stop`)**: An administrative kill switch that immediately freezes all agent execution across the entire control plane.
