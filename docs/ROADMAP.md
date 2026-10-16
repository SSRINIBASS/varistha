# Varistha Project Roadmap

This document outlines the architectural roadmap and upcoming milestone releases for Varistha.

---

## Current Release: v0.1.0 (Core Foundation & AgentOps)

- [x] Declarative Agent Spec (`apiVersion: varistha/v1`) with semver snapshots.
- [x] Immutable lifecycle stage promotion gates (Draft &rarr; Prototype &rarr; Staging &rarr; Production).
- [x] Durable LangGraph execution adapter with multi-trigger dispatch (manual, schedule, webhook).
- [x] Model gateway via LiteLLM supporting OpenAI, Anthropic, Ollama, and vLLM.
- [x] Model Context Protocol (MCP) plugin architecture with 8 built-in plugins.
- [x] 7 production-tested Role Packs (`lead-research`, `competitor-intel`, `outbound-sdr`, etc.).
- [x] Human-in-the-loop approvals inbox with side-by-side proposed/edited diffs.
- [x] Policy engine with input/output guardrails (PII redaction, injection scans, schema validation).
- [x] Token economics: per-run, per-day budgets, and emergency global kill switch.
- [x] OpenTelemetry GenAI spans with fan-out to Langfuse and Grafana Tempo.
- [x] Multi-user RBAC (`admin`, `operator`, `viewer`) and AES-256-GCM encrypted secrets vault.
- [x] Zero-dependency Docker Compose deployment and one-line installers.

---

## Milestone v0.2.0 (Distributed Scaling & Workflows)

**Target: Q1 2027**

### 1. Runtime Pluggability
- **Hatchet / Temporal Adapter**: Alternative distributed runtime engine behind the `Runtime` interface for long-running workflows spanning multiple days.
- **Worker Auto-Scaling**: Dynamic worker pool scaling based on task queue depth.

### 2. Ecosystem Expansion
- **Official Slack & Discord Plugins**: Interactive agent triggers and approval requests delivered directly into company chat channels.
- **Google Workspace & Office 365 MCP Plugins**: Calendar event scheduling, Google Docs generation, and Drive synchronization.
- **PostgreSQL Read-Only Analytics Plugin**: Safe SQL querying with read-only transaction locks and schema introspection.

### 3. Eval Dataset Synthesis
- **Diff-to-Eval Pipeline**: Automatically convert approved human edits from the Approvals Inbox into fine-tuning datasets and regression test cases.

---

## Milestone v0.3.0 (Enterprise Packaging & Team Collaboration)

**Target: Q2 2027**

### 1. Cloud-Native Packaging
- **Production Kubernetes Helm Chart**: Automated deployment with horizontal pod autoscalers (HPA), ingress controllers, and secret managers.
- **AWS / GCP Terraform Modules**: Infrastructure-as-code blueprints for managed PostgreSQL (RDS/Cloud SQL) and container deployments.

### 2. Identity & Governance
- **SSO / OIDC Authentication**: Single sign-on integration with Okta, Google Workspace, Zitadel, and Keycloak.
- **Multi-Tenant Team Workspaces**: Granular team-level workspace partitioning and cross-functional role delegation.
- **Audit Compliance Export**: Automated SOC 2 and ISO 27001 audit report exports.

---

## Milestone v1.0.0 (Autonomous Collective & Production Hardening)

**Target: H2 2027**

- **Multi-Agent Collaboration Graphs**: Inter-agent communication protocols with delegated tasks, shared memory caches, and hierarchical approvals.
- **Automated Adversarial Red-Teaming**: Scheduled continuous prompt injection fuzzing and jailbreak defense evaluation.
- **Edge Deployment**: Ultra-lightweight standalone single-binary distributions for air-gapped environments.

---

## Contributing to the Roadmap

Have a feature request or architectural proposal?
- Propose new MCP plugins via the [Plugin Proposal Template](https://github.com/SSRINIBASS/varistha/issues/new?template=plugin_proposal.yml).
- Join architectural discussions in our [GitHub Discussions](https://github.com/SSRINIBASS/varistha/discussions).
