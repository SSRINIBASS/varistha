# Plan: Phase 7 Task 3 — Comprehensive Guides & Documentation Suite

## Objective
Author the complete developer and operator documentation suite for Varistha v0.1.0 as specified in `docs/SPEC.md § 6`.

## Scope of Documentation Files
1. **`docs/guides/quickstart.md`**:
   - 5-minute zero-dependency quickstart with Docker Compose.
   - Initializing and applying an agent spec via CLI.
   - Inspecting running agents, live OTel trace waterfall, and approval inbox in UI.
2. **`docs/guides/concepts.md`**:
   - The Three Pillars: Build, Run, Govern.
   - Lifecycle stages: Draft, Prototype, Staging, Production, Deprecated, Retired.
   - Promotion gates and eval score thresholds.
   - Autonomy Levels (L0 Manual, L1 Action Approval, L2 Supervised, L3 Monitored, L4 Autonomous).
   - Policy Engine: Input filters (PII, injection), Output schemas, Outbound tool approval.
   - Spending limits: per-run, per-day budgets, and emergency circuit breakers.
3. **`docs/guides/role-packs.md`**:
   - Built-in role packs overview (`lead-research`, `competitor-intel`, `outbound-sdr`, etc.).
   - Role pack anatomy: spec YAML, prompts, eval suite, plugin configurations.
   - Authoring custom role packs.
4. **`docs/guides/plugin-authoring.md`**:
   - Model Context Protocol (MCP) plugin architecture.
   - Manifest specification (`manifest.json` schema).
   - Tool definition, input/output schemas, and execution handling.
   - Security constraints: SSRF private address denylists, untrusted data labeling.
5. **`docs/guides/production-hardening.md`**:
   - Production deployment topology (Postgres + pgvector, API, Worker, UI, Reverse Proxy).
   - TLS termination with Caddy / Nginx.
   - Secrets management with AES-256-GCM master key derivation.
   - Backup & disaster recovery automation.
   - OpenTelemetry Collector fan-out to Langfuse and Grafana Tempo.
6. **`docs/guides/api-reference.md`**:
   - Comprehensive endpoint reference organized by bounded context:
     - Registry (`/api/v1/agents`, `/versions`, `/stages`, `/diff`)
     - Runtime (`/api/v1/agents/{id}/runs`, `/runs/{id}`, `/traces/{trace_id}`)
     - Governance (`/api/v1/approvals`, `/policies`, `/budgets`, `/evals`)
     - Identity & Auth (`/api/v1/auth/keys`, `/auth/secrets`, `/auth/me`)

## Verification
- Add documentation consistency test in `apps/api/src/shared/tests/test_docs_integrity.py` verifying all referenced links, code blocks, and markdown structure.
- `python scripts/check_boundaries.py`
- `uv run ruff check .`
- `uv run pyright apps/api`
- `uv run pytest apps/api/src/shared/tests/test_docs_integrity.py`
