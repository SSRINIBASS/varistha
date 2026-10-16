# Varistha Example Agents Sandbox

This directory contains standalone, production-validated Agent Specifications demonstrating key Varistha architectural patterns:
- Multi-model routing (primary model with automated fallback).
- Pluggable Model Context Protocol (MCP) tool integrations.
- Autonomy tiering (L1 action approval vs L2 supervised).
- Guardrails (PII redaction, prompt injection defense, schema enforcement).
- Hard budget limits (per-run and per-day caps).

---

## Example Agent Specifications

| File | Purpose | Autonomy | Triggers | Plugins |
|---|---|---|---|---|
| **[`lead-researcher.yaml`](lead-researcher.yaml)** | B2B lead enrichment & personalized outreach | `L1` (Approval required) | `manual` | `web-fetch`, `email-draft` |
| **[`competitor-intel.yaml`](competitor-intel.yaml)** | Pricing and changelog monitor | `L2` (Supervised) | `schedule` (Daily 06:00), `manual` | `web-search`, `web-scrape`, `crm-export` |
| **[`support-triager.yaml`](support-triager.yaml)** | Inbound support ticket triage & response drafting | `L1` (Approval required) | `webhook`, `manual` | `web-fetch`, `email-draft` |

---

## How to Run Examples

### 1. Validate and Register
Register an example spec into your running control plane:

```bash
# Register the lead researcher
varistha apply -f examples/lead-researcher.yaml

# Register the competitor monitor
varistha apply -f examples/competitor-intel.yaml

# Register the support triager
varistha apply -f examples/support-triager.yaml
```

### 2. Trigger Execution
Submit execution runs with custom inputs:

```bash
# Run lead researcher
varistha run lead-researcher --input '{"domain": "stripe.com"}'

# Run support triager
varistha run support-triager --input '{"ticket_id": "TCK-1042", "text": "Unable to export CSV logs"}'
```

### 3. Review Approvals and Traces
- Open the Dashboard: [http://localhost:3000](http://localhost:3000)
- View pending approvals in the Approvals Inbox ([http://localhost:3000/approvals](http://localhost:3000/approvals))
- Inspect execution traces and span waterfalls ([http://localhost:3000/runs](http://localhost:3000/runs))
