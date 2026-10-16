# Changelog

All notable changes to Varistha will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-16

Initial public release of Varistha: an open-source, self-hostable control plane to build, run, monitor, and govern autonomous AI agents (AI employees) for startups.

### Phase 7 — Docs, Packaging and Launch

- `docs/checkpoints/2026-10-16-phase-7-complete.md`: Formal Phase 7 completion checkpoint certifying all seven phases of Varistha and authorizing release tags `v0.1.0` and `phase-7-complete`.
- `docs/launch/launch-playbook.md`: Comprehensive public launch kit including core positioning narrative, Hacker News "Show HN" copy and story lead, Reddit posts for `r/selfhosted` and `r/LocalLLaMA`, Product Hunt launch kit, social media launch threads, and community feedback triage protocols.
- `docs/ROADMAP.md`: Public architectural roadmap for Varistha detailing upcoming releases: v0.2.0 (Hatchet/Temporal distributed runtime adapters, Slack/Discord MCP plugins), v0.3.0 (Kubernetes Helm chart, diff-to-eval synthesis), and v1.0.0 (collaborative multi-agent collective and continuous red-teaming).
- `apps/api/src/shared/tests/test_launch_assets.py`: Automated test suite validating launch playbook copies, channel sections, quickstart references, and roadmap milestone integrity.

- `examples/`: Ready-to-run sandbox agent specifications and documentation:
  - `lead-researcher.yaml`: B2B lead enrichment & personalized outreach agent (Autonomy L1 with human approval gate).
  - `competitor-intel.yaml`: Market intelligence & pricing monitor with daily cron schedule trigger (Autonomy L2).
  - `support-triager.yaml`: Customer support triage and response drafter with webhook trigger (Autonomy L1).
  - `README.md`: Sandbox execution guide explaining registration, triggering runs, and reviewing approvals.
- `packages/spec/tests/test_examples_validity.py`: Automated test suite validating that all `examples/*.yaml` strictly conform to the `varistha-spec` Pydantic models.

- `docs/guides/`: Complete operator and developer documentation suite:
  - `quickstart.md`: 5-minute quickstart from zero dependencies to running first agent with approval and OTel trace stream.
  - `concepts.md`: Deep dive on Three Pillars (Build, Run, Govern), Lifecycle stages (Draft, Prototype, Staging, Production, Deprecated, Retired), Autonomy levels (L0 to L4), Policy Engine, and Spending Limits.
  - `role-packs.md`: Operational guide to prebuilt AI employee packs (`lead-research`, `competitor-intel`, `outbound-sdr`, `support-responder`, `content-repurposer`, `lead-qualifier`, `chief-of-staff`) and custom pack authoring.
  - `plugin-authoring.md`: Architecture guide for creating Model Context Protocol (MCP) plugins, manifest schemas, SSRF defenses, and untrusted data labeling.
  - `production-hardening.md`: Production deployment guide covering Caddy/Nginx reverse proxy, TLS termination, AES-256-GCM encryption at rest, automated backup crons, and emergency kill switches.
  - `api-reference.md`: Comprehensive REST API documentation organized by bounded context (Registry, Runtime, Governance, Identity/Auth, Plugins).
- `apps/api/src/shared/tests/test_docs_integrity.py`: Automated test suite ensuring documentation suite completeness, proper markdown H1 formatting, and resolving relative links.

- `scripts/install.sh`: One-line automated installation script for Linux and macOS (`curl -fsSL https://get.varistha.dev/install.sh | bash`), verifying git, docker, and python/uv, cloning repository, provisioning `deploy/.env`, and installing the `varistha` CLI.
- `scripts/install.ps1`: One-line automated installation script for Windows PowerShell (`irm https://get.varistha.dev/install.ps1 | iex`), verifying system prerequisites, configuring environment, and installing the `varistha` CLI.
- `packages/cli/tests/test_packaging_and_scripts.py`: Automated test suite validating CLI version output (`varistha --version`), subcommands help catalog (`init`, `apply`, `run`, `diff`, `approvals`, `budget`, `kill`, `resume`, `emergency-stop`, `policies`, `eval`), and installation script integrity.
- `README.md`: Flagship open-source control plane landing page with badges, ASCII architecture flow diagram, core capabilities breakdown (Build, Run, Govern), 5-minute quickstart, CLI workflow, role packs showcase, and security disclosures.
- `CONTRIBUTING.md`: Expanded contributor guidelines including bounded context architecture rules, outside-the-model enforcement principles, OSI-approved license constraints, and pre-PR verification gates.
- `.github/pull_request_template.md`: Added verification item for OSI-approved licenses on all new dependencies.
- `.github/ISSUE_TEMPLATE/plugin_proposal.yml`: Added GitHub issue template for community MCP plugin proposals with license and autonomy risk categorization.
- `.github/workflows/release.yml`: Automated CI/CD release workflow triggered on `v*` tags building multi-arch Docker container images (`api`, `worker`, `ui`) pushed to GitHub Container Registry (GHCR) and Python distribution wheels for PyPI.
- `apps/api/src/shared/tests/test_repo_hygiene.py`: Automated test suite validating open-source licensing (Apache-2.0 across all packages), presence of mandatory hygiene documentation, issue templates YAML validity, and release workflow integrity.

### Phase 6 — Hardening, Security, Auth & OTel Fan-Out

- `apps/api/src/identity/`: Multi-user RBAC system (`admin`, `operator`, `viewer`) with API key authentication:
  - `models.py`: `Role` enumeration with strict hierarchy (`admin` > `operator` > `viewer`) and `Identity` representation with `has_role` permission checks.
  - `schemas.py`: Pydantic request/response schemas (`CreateApiKeyRequest`, `ApiKeyResponse`, `CreatedApiKeyResponse`, `CurrentIdentityResponse`).
  - `service.py`: High-entropy token generation (`var_live_` prefix + 32-byte secret), SHA-256 constant-time hashing, key creation, listing, revocation, and authentication verification.
  - `dependencies.py`: Request authentication supporting `X-API-Key` and `Authorization: Bearer <key>` headers, with automated development-admin fallback when `auth_enabled=False` and strict denial when `auth_enabled=True`. Dependency factory `require_role(minimum_role)`.
  - `router.py`: REST routes for API key management (`POST /api/v1/auth/keys`, `GET /api/v1/auth/keys`, `DELETE /api/v1/auth/keys/{id}`, `GET /api/v1/auth/me`).
  - `tests/test_auth.py`: Comprehensive test suite for key generation, role hierarchy comparisons, database lifecycle, RBAC endpoints, and auth-enabled enforcement.
- `apps/api/src/shared/crypto.py`: Authenticated AES-256-GCM symmetric encryption at rest:
  - HKDF-SHA256 deterministic master key derivation from `secret_key` or explicit `encryption_key`.
  - Nonce generation using cryptographically secure random bytes (96-bit unique IV per operation).
  - Versioned ciphertext serialization (`v1:<base64(nonce + ciphertext + tag)>`) with tamper detection and typed exceptions (`CryptoError`, `DecryptionError`).
  - Unit tests verifying deterministic key derivation, roundtrip encryption, unique nonces, tamper resistance, and associated data verification (`apps/api/src/shared/tests/test_crypto.py`).
- `apps/api/src/shared/db/models/secrets.py`: `Secret` SQLAlchemy model for encrypted secrets vault with indexed unique name, encrypted ciphertext payload, description, and audit timestamps.
- `apps/api/alembic/versions/0007_secrets_vault.py`: Alembic migration creating `secrets` table with unique index on `name`.
- `apps/api/src/identity/`: Secrets management service and REST endpoints:
  - `secrets_service.py`: `store_secret`, `resolve_secret`, `list_secrets`, and `delete_secret` with seamless AES-256-GCM encryption/decryption.
  - `schemas.py`: `CreateSecretRequest`, `SecretMetadataResponse` (securely omitting secret values), and `SecretValueResponse`.
  - `router.py`: REST routes `POST /api/v1/auth/secrets` (Admin only), `GET /api/v1/auth/secrets` (Operator/Admin), `GET /api/v1/auth/secrets/{name}` (Admin only), and `DELETE /api/v1/auth/secrets/{name}` (Admin only).
  - `tests/test_secrets.py`: Integration and RBAC test suite validating vault lifecycle, encrypted at rest storage, zero-leak metadata listings, and role boundary enforcement.
- `docs/security/`: Formal threat modeling and security architecture documentation:
  - `threat-model.md`: Detailed STRIDE and OWASP Top 10 for LLM Applications (2025) threat model covering indirect prompt injection, SSRF, outbound tool approval bypassing, telemetry credential leakage, and runaway agent defenses.
  - `checklist.md`: Operational production readiness checklist auditing authentication, encryption at rest, untrusted output quarantine, SSRF denylists, and compliance guardrails.
- `apps/api/src/shared/guardrails/builtin/injection.py`: Strengthened override patterns to detect system instruction overrides, delimiter tampering, and rules circumvention.
- `apps/api/src/shared/tests/test_security_audit.py`: End-to-end automated security verification suite testing all 7 core invariants (SSRF IP matrix, prompt injection quarantine, outbound approval enforcement, zero-secret telemetry redaction, AES-256-GCM tamper defense, vault zero-leakage, and RBAC boundary denial).
- `deploy/otel-collector-config.yaml`: CNCF OpenTelemetry Collector Contrib configuration routing OTLP traces (gRPC :4317, HTTP :4318) through memory limiters and batch processors, fanning out to Varistha (`/v1/traces`), Langfuse, and Grafana Tempo.
- `deploy/docker-compose.yml` & `deploy/docker-compose.otel.yml`: Added optional `otel` Compose profile so that default `docker compose up` strictly retains 4 core containers while `docker compose --profile otel up` launches the OTel Collector.
- `deploy/.env.example`: Documented external observability fan-out variables (`OTEL_EXPORTER_OTLP_ENDPOINT`, `LANGFUSE_HOST`, `LANGFUSE_AUTH_HEADER`, `TEMPO_OTLP_ENDPOINT`).
- `apps/api/src/shared/telemetry/`: Added OTLP HTTP batch exporter attachment (`opentelemetry-exporter-otlp-proto-http`) to `init_tracer_provider()`, supporting `OTEL_EXPORTER_OTLP_ENDPOINT` with graceful fallbacks.
- `docs/observability/otel-fanout.md`: Full architecture, integration guides, and zero-leakage telemetry redaction documentation.
- `apps/api/src/shared/tests/`: Added unit test suites `test_otel_collector_config.py` and `test_telemetry_export.py`.
- `apps/api/src/runtime/tests/test_concurrency_load.py`: High-concurrency automated test suite validating 10+ concurrent agents executing runs, writing spans, triggering approval interrupts, and maintaining strict contextvar trace isolation under parallel bursts.
- `scripts/load_test_concurrency.py`: Standalone CLI benchmarking tool with asynchronous worker pool, latency percentile analysis (p50, p90, p95, p99), and throughput measurement.
- `docs/runbooks/backup-and-restore.md`: Production runbook for PostgreSQL & pgvector backup, point-in-time recovery, Alembic migration verification, and master encryption key disaster recovery.
- `scripts/backup_postgres.sh`: Automated backup script for PostgreSQL and pgvector with SHA-256 checksum generation.
- `docs/checkpoints/2026-10-16-phase-6-complete.md`: Formal Phase 6 checkpoint document certifying all Phase 6 exit criteria are satisfied (git tag `phase-6-complete`).





### Phase 5 — Plugin Ecosystem & Role Packs

- `apps/api/src/plugins/`: Plugin manifest registry and capability discovery API:
  - `schemas.py`: Pydantic response models `PluginInfoResponse` and `PluginListResponse` exposing metadata, risk level, scopes, untrusted output quarantine, and configuration schema.
  - `host.py`: Added discovery helpers `get_tools_for_plugin` and `get_config_schema` to enumerate exposed tool capabilities and JSON configuration schemas.
  - `router.py`: REST endpoints `GET /api/v1/plugins` and `GET /api/v1/plugins/{name}`.
  - `tests/test_router.py`: Unit and integration test suite covering plugin enumeration, detail retrieval, error handling, and host dependency injection.
- `apps/ui/src/app/plugins/page.tsx`: Plugins & Capability Management control plane hub:
  - Summary KPI cards (Installed Plugins, Low Risk, Approval Gated, Untrusted Output Quarantined).
  - Subnav underline tabs for `Plugin Directory` and `Security Architecture` documentation.
- `apps/ui/src/components/plugins/`:
  - `plugin-card.tsx`: Card component displaying plugin metadata, transport tags, semantic risk badges, approval gating badges, untrusted output flags, permission scopes, and tool chips.
  - `plugin-inspector.tsx`: Tabbed modal inspector for governance properties, JSON Schema configuration, and raw plugin manifests.
  - `plugin-explorer.tsx`: Searchable and filterable plugin catalog supporting search by keyword and filtering by risk level, transport type, and approval policy.
- `apps/ui/src/components/badges.tsx`: Added `PluginRiskBadge` (`low`, `medium`, `high`) and `ApprovalRequiredBadge` (`Approval Required`, `Auto-Executable`).
- `apps/ui/src/components/navbar.tsx`: Added `Plugins` navigation item with `Blocks` icon.
- `apps/ui/src/__tests__/plugins.test.tsx`: Comprehensive unit tests for badges, card interactions, inspector modal tabs, and explorer filters.
- `plugins/web-search/`: Web search plugin:
  - `plugin.yaml`: Manifest declaration (`scopes: [network:read]`, `risk: low`, `untrusted_output: true`).
  - `config.schema.json`: JSON configuration schema supporting `duckduckgo`, `searxng`, and `mock` engines.
  - `searcher.py`: Query execution, DuckDuckGo HTML parser, redirect link normalization, and deterministic mock engine.
  - `tests/test_searcher.py`: Unit tests for search execution, HTML parsing, and mock mode.
- `plugins/web-scrape/`: Deep webpage and article scraper plugin:
  - `plugin.yaml`: Manifest declaration (`scopes: [network:read]`, `risk: low`, `untrusted_output: true`).
  - `config.schema.json`: JSON configuration schema for character limits and heading/link extraction flags.
  - `ssrf.py`: Strict SSRF defense blocking loopback, RFC 1918 private subnets, link-local, and cloud metadata.
  - `scraper.py`: Content extraction, clean markdown conversion, metadata parsing, and hyperlink normalization.
  - `tests/test_scraper.py`: Unit tests for SSRF enforcement, markdown conversion, and metadata extraction.
- `plugins/crm-export/`: CRM and lead export plugin:
  - `plugin.yaml`: Manifest declaration (`scopes: [storage:write]`, `risk: medium`).
  - `config.schema.json`: JSON configuration schema for export formats.
  - `exporter.py`: Exporter supporting CSV (with header normalization), HubSpot batch contacts, Salesforce Lead sObjects, and JSON formats, with strict lead identifier validation.
  - `tests/test_exporter.py`: Unit tests for validation rules, CSV generation, and CRM payload schemas.
- `plugins/email-draft/`: Contextual email composer plugin:
  - `plugin.yaml`: Manifest declaration (`scopes: [email:draft]`, `requires_approval: false`).
  - `config.schema.json`: JSON configuration schema for tone, sender name, and signature templates.
  - `composer.py`: Contextual email composer supporting token interpolation (`{{first_name}}`, `{{company}}`, `{{topic}}`, `{{call_to_action}}`), tone styling, and inbox preview generation.
  - `tests/test_composer.py`: Unit tests for token interpolation, email address validation, and tone rendering.
- `plugins/email-send/`: Outbound email transmission plugin:
  - `plugin.yaml`: Manifest declaration (`scopes: [email:send]`, `requires_approval: true`).
  - `config.schema.json`: JSON configuration schema for providers (`mock`, `smtp`, `resend`, `sendgrid`), sender email, suppression lists, and dry-run flag.
  - `sender.py`: Dispatch engine with mandatory suppression/opt-out list enforcement (CAN-SPAM/GDPR/DPDP compliance), email validation, and deterministic mock delivery simulation.
  - `tests/test_sender.py`: Unit tests for approval gating flag, recipient validation, opt-out suppression blocking, and simulated dispatch.
- `plugins/x-post/`: Outbound social publishing plugin for X (Twitter):
  - `plugin.yaml`: Manifest declaration (`scopes: [x:write, social:post]`, `requires_approval: true`).
  - `config.schema.json`: JSON configuration schema for official API keys and mock mode.
  - `x_poster.py`: Publishing engine with strict character length validation (1 to 280 characters), thread reply support, and deterministic simulation.
  - `tests/test_x_poster.py`: Unit tests for 280 character limit enforcement, empty post rejection, and simulated status updates.
- `plugins/linkedin-post/`: Outbound professional publishing plugin for LinkedIn:
  - `plugin.yaml`: Manifest declaration (`scopes: [linkedin:write, social:post]`, `requires_approval: true`).
  - `config.schema.json`: JSON configuration schema for OAuth credentials, visibility, and mock mode.
  - `linkedin_poster.py`: Publishing engine with character length validation (1 to 3000 characters), visibility options (`PUBLIC`, `CONNECTIONS`), and article attachment support.
  - `tests/test_linkedin_poster.py`: Unit tests for character limit enforcement, visibility validation, and simulated share updates.
- `apps/api/src/plugins/definitions.py`: Extracted LiteLLM function calling schemas for all 8 core plugins, keeping `PluginHost` under 300 lines (273 lines).
- `apps/api/src/plugins/host.py`: Registered handlers for all communication tools and delegated schema generation to `definitions.py`.
- `apps/api/src/runtime/adapter.py`: Refined runtime approval interception so that internal drafts run autonomously at L1 while outbound actions (`send_email`, `email_send`, `x_post`, `linkedin_post`) require human approval.
- `docs/adr/0022-outbound-and-communication-plugins.md`: Architecture Decision Record for outbound and communication plugins.
- `apps/api/src/plugins/host.py`: Wired handlers and OpenAI/LiteLLM function calling definitions for `web_search`, `web_scrape`, and `crm_export`.
- `docs/adr/0021-core-research-and-data-plugins.md`: Architecture Decision Record for core research and data plugins.
- `docs/plans/phase-5-task-2-core-research-and-data-plugins.md`: Task plan and acceptance verification record.
- `role-packs/lead-research/`: Lead Researcher & ICP Finder role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_lead_researcher.py`).
  - 4-pillar ICP scoring matrix (Firmographic, Technographic, Intent/Growth Signals, Authority/Role fit).
- `role-packs/lead-qualifier/`: Inbound Lead Qualifier & Scorer role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_lead_qualifier.py`).
  - BANT & MEDDPICC qualification frameworks, intent classification, and tier routing matrix.
- `role-packs/outbound-sdr/`: Outbound SDR & Multi-Channel Copywriting role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_outbound_sdr.py`).
  - Lavender 90+ behavioral copywriting framework, 3-touch sequence, and mandatory approval gates.
- `role-packs/competitor-intel/`: Competitor Intelligence & Diff Watcher role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_competitor_intel.py`).
  - Multi-vector semantic diffing (`PRICING_CHANGE`, `FEATURE_RELEASE`, `POSITIONING_PIVOT`), threat severity ratings, and automated sales battlecards.
- `role-packs/content-repurposer/`: Content Repurposer & Multi-Channel Distribution role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_content_repurposer.py`).
  - 5-asset transformation framework (X thread, LinkedIn carousel, 2x standalone snippets, newsletter segment, 5-slide narrative deck).
- `role-packs/support-responder/`: Tier-1 Support Responder & Technical Triage role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_support_responder.py`).
  - Intent classification taxonomy, urgency SLA matrix, grounded technical troubleshooting, and escalation routing.
- `role-packs/chief-of-staff/`: Executive Chief of Staff role pack:
  - Canonical `agent.yaml` specification, system prompts, evaluation benchmark suite (`evals/suite.yaml`), and conformance test suite (`tests/test_chief_of_staff.py`).
  - 4-pillar executive synthesis (Decision Records, Action Item Matrix, Functional Radar, CEO Morning Briefing).

### Phase 4 — Evals & Confidence

- `apps/ui/src/app/evals/page.tsx`: Evaluations & Verifiable Confidence control plane hub:
  - Subnav tabs for `suites`, `runs`, `regression`, and `confidence`.
  - Summary KPI cards (Registered Suites, Total Executions, Average Pass Rate, Active Regressions).
  - Empty, loading, and error states with manual data refresh and execution workflow.
- `apps/ui/src/components/evals/`:
  - `eval-suite-runner.tsx`: Suite runner and catalog with test case counts, evaluator breakdown, and modal execution trigger supporting version snapshot pinning.
  - `eval-run-detail.tsx`: Granular test execution explorer with pass rate progress gauge, latency metrics, searchable assertions table with status filters, and assertion inspector modal.
  - `eval-regression-view.tsx`: Version-over-version regression comparator displaying pass rate deltas, regression and improvement counters, and test case verdict breakdown.
  - `confidence-sandbox.tsx`: Verifiable confidence & review-priority sandbox evaluating output payloads across multi-source verifiable signals (JSON schema, grounding context, eval benchmarks, approval history).
- `apps/ui/src/components/badges.tsx`: Semantic badge components `ReviewPriorityBadge` (`low`, `medium`, `high`, `critical`) and `RegressionStatusBadge` (`improved`, `regressed`, `added`, `removed`, `unchanged`).
- `apps/ui/src/components/navbar.tsx`: Top-level `Evals` navigation link with `FlaskConical` icon.
- `apps/ui/src/__tests__/evals.test.tsx`: Comprehensive unit tests for eval badges, runner, assertion inspector, regression comparator, and confidence sandbox.
- `docs/plans/phase-4-task-4-evals-and-confidence-ui.md`: Implementation plan and exit verification record.
- `apps/api/src/governance/confidence/`: Verifiable review-priority and confidence engine:
  - `engine.py`: `ReviewPriorityEngine` calculating multi-source verifiable confidence signals (JSON schema conformity, grounding keyword/citation overlap, offline eval benchmark pass rate, historical human approval rate) and review-priority classifications (`low`, `medium`, `high`, `critical`).
  - `schemas.py`: Pydantic models `ConfidenceSignal`, `ConfidenceEvaluationRequest`, and `ReviewPriorityOutcome`.
  - `router.py`: REST endpoint `POST /api/v1/governance/confidence/evaluate`.
- `apps/api/src/governance/evals/comparator.py`: Version regression comparator:
  - `compare_eval_runs`: Identifies regressed, improved, unchanged, added, and removed assertions between evaluation runs; computes pass rate delta and execution latency delta.
  - Endpoint `GET /api/v1/evals/compare` to retrieve version-over-version regression comparison reports.
- `apps/api/src/registry/gates.py` & `service.py`: Evaluation promotion gate enforcement:
  - Extended `evaluate_stage_transition` with `eval_runs` evaluation.
  - Strictly blocks promotion from `prototype` to `staging` unless at least one completed eval run achieves `pass_rate >= min_pass_rate`.
  - Strictly enforces `eval_score_threshold` against real completed `EvalRun` records for `staging` to `production` promotions.
  - Queries latest evaluation runs via `shared.db.models.eval` without violating bounded context isolation rules.
- `docs/adr/0019-review-priority-and-regression-comparator.md`: Architecture Decision Record for review-priority confidence, regression comparator, and promotion gates.
- `docs/plans/phase-4-task-3-review-priority-and-regression-comparator.md`: Plan and verification record.
- `apps/api/src/governance/evals/evaluators/`: Builtin evaluator library implementing the `BaseEvaluator` contract:
  - `ExactMatchEvaluator`: Strict value and whitespace-stripped deep equality assertions.
  - `ContainsEvaluator`: Substring, dictionary key-value, and list element presence verification.
  - `RegexEvaluator`: Pattern-matching assertions with graceful error detection.
  - `JsonSchemaEvaluator`: Structural dictionary and JSON-string conformity validation via `jsonschema`.
  - `GroundingEvaluator`: Keyword and citation overlap ratio calculation against input context.
  - `LLMRubricEvaluator`: LLM-as-a-judge scoring and rationale parsing using LiteLLM model gateways.
  - `create_evaluator`: Dynamic evaluator instantiation factory from declarative suite configurations.
- `apps/api/src/governance/evals/engine.py`: `EvalExecutionEngine` executing test cases against target agent specifications, applying matching evaluators, computing aggregate pass rates, and persisting granular `eval_results`.
- `apps/api/src/governance/evals/router.py`: REST endpoint `POST /api/v1/evals/suites/{id}/execute` to trigger offline evaluation runs.
- `packages/cli/src/varistha_cli/commands/eval_cmd.py`: CLI evaluation commands:
  - `varistha eval list [--agent <agent>] [--json]`: Lists registered evaluation suites.
  - `varistha eval run <suite_id_or_file> [--version <version>] [--json]`: Runs offline evaluations from database suite UUID or local YAML spec file, rendering a formatted Rich summary panel and granular assertion table. Exits with code 1 if pass rate falls below 80%.
- `docs/adr/0018-eval-execution-engine-and-evaluators.md`: Architecture Decision Record for eval execution engine, evaluators library, and CLI.
- `docs/plans/phase-4-task-2-eval-execution-engine.md`: Task plan and acceptance criteria verification.
- `packages/spec/src/eval_models.py`: Declarative Pydantic schema for `varistha/v1 EvalSuite` with `EvaluatorConfig` (exact-match, contains, regex, json-schema, semantic-similarity, llm-rubric) and `TestCaseConfig` datasets.
- `apps/api/src/shared/db/models/eval.py`: SQLAlchemy models `EvalSuite`, `EvalRun`, and `EvalResult` with cascade deletions and JSON/JSONB support.
- `apps/api/alembic/versions/0005_evals.py`: Database migration creating `eval_suites`, `eval_runs`, and `eval_results` tables and indexes.
- `apps/api/src/governance/evals/`: Evaluation domain services and endpoints under `/api/v1/evals`:
  - `schemas.py`: Pydantic validation schemas (`EvalSuiteCreate`, `EvalSuiteResponse`, `EvalRunCreate`, `EvalResultCreate`, `EvalRunDetailResponse`).
  - `service.py`: Domain services for suite registration, run initialization, results recording, and pass rate aggregation.
  - `router.py`: REST endpoints `POST /api/v1/evals/suites`, `GET /api/v1/evals/suites`, `GET /api/v1/evals/suites/{id}`, `POST /api/v1/evals/runs`, `POST /api/v1/evals/runs/{id}/results`, `GET /api/v1/evals/runs`, `GET /api/v1/evals/runs/{id}`.
- `docs/adr/0017-eval-suite-schema-and-datasets.md`: Architecture Decision Record for eval suites and results storage.
- `docs/plans/phase-4-task-1-eval-suite-schema-and-datasets.md`: Task plan and exit criteria verification.

### Phase 3 — Governance & Boundaries

#### Added
- `apps/api/src/shared/db/models/approval.py`: `Approval` SQLAlchemy model linked to `runs` and `agents` with SQLite/PostgreSQL JSON/JSONB support.
- `apps/api/alembic/versions/0003_approvals.py`: Migration creating `approvals` table and cascade relationships.
- `apps/api/src/governance/approvals/`: Complete approval management domain within the `governance` bounded context:
  - `schemas.py`: Pydantic validation schemas (`ApprovalResponse`, `ApprovalListResponse`, `ApprovalResolveRequest`).
  - `service.py`: Domain services with `compute_payload_diff` recursive JSON difference calculator and resolution actions (`approve`, `reject`, `edit`).
  - `router.py`: REST endpoints `GET /api/v1/approvals`, `GET /api/v1/approvals/{id}`, and `POST /api/v1/approvals/{id}/resolve`.
- `apps/api/src/runtime/adapter.py` & `service.py`: Outside-the-model runtime interruption engine:
  - Halts execution when autonomy `L0` or `L1` agents invoke outbound tools or actions flagged `requires_approval: true`.
  - Transitions run status to `waiting_approval` with `completed_at=None`.
  - Emits OpenTelemetry `approval.wait` trace span with `varistha.approval_required=True` and `varistha.approval_status="pending"`.
- `packages/cli`: CLI approval governance commands:
  - `varistha approvals list`: View pending and resolved approvals in formatted Rich table.
  - `varistha approvals get <id>`: Inspect proposed payload, action type, and status details.
  - `varistha approvals approve <id>`: Authorize execution and complete run.
  - `varistha approvals reject <id>`: Abort run with operator rationale.
  - `varistha approvals edit <id> --payload '<json>'`: Modify proposed payload with field-level diff computation.
- `apps/api/src/shared/db/models/setting.py`: `SystemSetting` model for platform-wide control plane dynamic settings including global emergency stop.
- `apps/api/src/shared/db/models/agent.py`: Extended `Agent` entity with `is_active`, `kill_switch_tripped`, `kill_switch_reason`, and `kill_switch_tripped_at`.
- `apps/api/alembic/versions/0004_budgets_and_killswitch.py`: Database migration with SQLite batch table alteration and `system_settings` table.
- `apps/api/src/governance/budgets/`: Isolated budget management and circuit-breaker service within the `governance` bounded context:
  - `schemas.py`: Pydantic models `AgentBudgetStatusResponse`, `KillSwitchRequest`, `KillSwitchResponse`, `GlobalKillSwitchRequest`, `GlobalKillSwitchStatus`.
  - `service.py`: Domain services with daily rolling spend aggregation (`get_daily_spend`), agent budget status, agent kill/resume switches, and global emergency stop toggle.
  - `router.py`: REST endpoints `GET /api/v1/agents/{id}/budget`, `POST /api/v1/agents/{id}/kill`, `POST /api/v1/agents/{id}/resume`, `GET /api/v1/system/kill-switch`, and `POST /api/v1/system/kill-switch`.
- `apps/api/src/runtime/adapter.py` & `service.py`: Outside-the-model financial circuit breaker and kill-switch enforcement:
  - Aborts execution with status `failed` and error `budget_exceeded: Run cost ($X) exceeded limit ($Y)` when `max_usd_per_run` is breached.
  - Rejects run initiation with HTTP 429 (`BudgetExceededError`) when UTC daily spend meets or exceeds `max_usd_per_day`.
  - Rejects run initiation with HTTP 409 (`KillSwitchTrippedError`) when agent kill switch is tripped or global emergency stop is active.
  - Tags root OpenTelemetry trace spans with `varistha.budget.exceeded = True` and `varistha.kill_switch_tripped = True`.
- `apps/api/src/shared/guardrails/`: Core Policy Framework and Built-in Policies:
  - `interface.py`: Core contracts `PolicyHook`, `PolicyAction`, `PolicyResult`, `PolicyContext`, and `BasePolicy`.
  - `registry.py`: `PolicyRegistry` with discovery and default policy registration.
  - `engine.py`: `PolicyEngine` orchestrating sequential evaluation, redaction chaining, block short-circuiting, and OpenTelemetry `guardrail.check` span generation.
  - `builtin/pii.py`: `PIIRedactionPolicy` for emails, phone numbers, credit card numbers with Luhn check, SSNs, API keys / bearer tokens, and IPv4 addresses across text and recursive JSON structures.
  - `builtin/injection.py`: `PromptInjectionPolicy` scanning for instruction overrides, jailbreak phrases, delimiter hijacking (`<system>`, `[INST]`, `### Instruction:`), and data exfiltration patterns.
  - `builtin/schema.py`: `SchemaValidationPolicy` verifying JSON string and dictionary schema conformity.
  - `builtin/unverified_claims.py`: `NoUnverifiedClaimsPolicy` detecting ungrounded absolute guarantees.
- `apps/api/src/governance/policies/`: Governance REST API endpoints:
  - `GET /api/v1/policies`: Lists all registered policies and supported hook points.
  - `POST /api/v1/policies/test`: Evaluates policies interactively against sample payloads.
- `apps/api/src/runtime/service.py` & `adapter.py`: Outside-the-model runtime guardrail interception:
  - Pre-flight `spec.guardrails.input` evaluation before runtime invocation, rejecting injection attacks with HTTP 422 (`PolicyViolationError`) or propagating sanitized input to execution context.
  - Post-execution `spec.guardrails.output` validation enforcing output schema conformity.
  - Telemetry: OpenTelemetry `guardrail.check` spans with `varistha.guardrail.*` semantic conventions.
- `packages/cli`: CLI inspection and testing commands:
  - `varistha policies list`: Formatted table of registered guardrails.
  - `varistha policies test <policy_name> -i <text>`: Interactively tests policies and outputs detailed outcomes and alerts.
- `apps/ui/src/app/governance/page.tsx`: Centralized Governance Control Room with real-time stats (Global Status, Pending Approvals, Halted Agents) and three-way subnavigation.
- `apps/ui/src/components/governance/approvals-inbox.tsx`: Human-in-the-Loop Approvals Inbox with status filtering, detail drawer, and one-click actions: Approve, Reject (with required rationale), and Edit & Approve.
- `apps/ui/src/components/governance/payload-diff-viewer.tsx`: GitHub-style unified diff viewer displaying green additions and red deletions for parameter changes.
- `apps/ui/src/components/governance/budgets-dashboard.tsx`: Budgets & Circuit Breakers board featuring platform Global Emergency Stop toggle, spend gauges against caps, and agent kill/resume controls.
- `apps/ui/src/components/governance/guardrails-explorer.tsx`: Guardrails Explorer with policy catalog and interactive live testing sandbox.
- `apps/ui/src/components/navbar.tsx`: Updated global navigation with Governance link, ShieldAlert icon, and dynamic pending approvals badge counter pill.
- `apps/ui/src/__tests__/governance.test.tsx`: Vitest suite covering inbox rendering, approvals resolution, diff viewer, budget progress, kill switch confirmation, and guardrail tester (32/32 tests passing).
- `docs/adr/0016-governance-dashboard-ui-and-approvals.md`: Architecture Decision Record for Governance UI and Human-in-the-Loop control plane.
- `docs/plans/phase-3-task-4-governance-ui.md`: Implementation plan and exit criteria verification for Phase 3 Task 4.
- `docs/adr/0015-guardrail-policy-engine-and-middleware.md`: ADR documenting guardrail policy engine, built-ins, and outside-the-model middleware.
- `docs/adr/0014-budget-tracking-and-circuit-breakers.md`: Architecture Decision Record for budget tracking, rate limits, and emergency kill switches.
- `docs/plans/phase-3-task-2-budgets-and-kill-switch.md`: Implementation plan and exit criteria verification for Phase 3 Task 2.


### UI & UX — GitHub Primer Design System & Theme Engine

#### Added
- Full-span responsive widescreen layout eliminating artificial `max-w-7xl` constraints, expanding Kanban board and tables to 100% monitor viewport.
- Official GitHub Primer design tokens for Light and Dark themes, including atmospheric ambient glow gradients, multi-layer elevation shadows, and GitHub font stack (`-apple-system`, `ui-monospace`).
- React 19 `useSyncExternalStore` theme provider with lazy `localStorage` initialization and inline anti-FOUC `<head>` script.
- GitHub `ActionMenu` styled `ThemeToggle` dropdown supporting Light, Dark, and System preference synchronization.
- GitHub repository navigation bar featuring `varistha / control-plane` breadcrumb, `/` command search bar, `API Online` pulse pill, and UnderlineNav with signature coral active indicator (`#fd8c73` / `#f78166`).
- GitHub Bento card architecture (`.gh-bento`, `.gh-bento-hero`, `.gh-box`, `.gh-counter`, `.gh-btn-primary`, `.gh-btn-secondary`, `.gh-btn-danger`, `.gh-btn-subtle`).
- GitHub Actions workflow run styling for `/runs` with real-time status icons, token counts, and cost telemetry.
- GitHub Pull Request styled Spec Diff Viewer with `gh-diff-add`/`gh-diff-delete` row highlights, base/compare branch pickers, and monospace values.
- `docs/adr/0012-github-primer-design-system.md`: Architectural Decision Record for GitHub Primer design system.
- `docs/checkpoints/2026-10-15-github-primer-ui-redesign.md`: Checkpoint log with end-to-end browser verification proofs.

### Phase 2 — Registry and Lifecycle

#### Added
- `packages/spec/src/diff.py`: Pure deterministic Spec Diffing Engine for comparing AgentSpec versions
  - Detects field-level deltas across metadata, role, models, instructions, autonomy, plugins, guardrails, budgets, triggers, and evals
  - Classifies changes as breaking vs non-breaking with explicit explanatory reasons (autonomy escalation, guardrail removal, primary model changes, budget reductions, plugin removal)
  - 100% test coverage with 21 unit tests in `packages/spec/tests/test_diff.py`
- `apps/api/src/registry/diff_service.py` & `router.py`: REST endpoints for spec version diffing
  - `GET /api/v1/agents/{id_or_name}/versions/{v1}/diff/{v2}`: Compares two published immutable versions
  - `POST /api/v1/agents/{id_or_name}/diff`: Previews candidate spec diff and breaking change warnings against current active or target base version
- `packages/cli`: `varistha diff` CLI command
  - Compares published versions (`varistha diff <agent> <v1> <v2>`) or local files (`varistha diff -f agent.yaml`)
  - Supports `--strict` gate to exit with non-zero code on breaking changes
  - Rich terminal formatting with color badges and breaking change alerts
- `docs/adr/0011-spec-diffing-engine-and-breaking-changes.md`: ADR documenting spec diffing architecture and breaking change taxonomy
- `apps/api/src/shared/db/models/stage_transition.py`: `StageTransition` model for immutable audit trail of agent lifecycle changes
- `apps/api/alembic/versions/0002_stage_transitions.py`: Alembic migration creating `stage_transitions` table with cascade delete and foreign key indexing
- `apps/api/src/registry/gates.py`: Pure domain gate evaluation engine for lifecycle transitions (`Draft` → `Prototype` → `Staging` → `Production` → `Deprecated` → `Retired`)
  - Evaluates spec validity, successful execution runs, owner presence, guardrail attachments, eval suite thresholds, budget spend caps, and kill-switch confirmations
  - Validates rollbacks and demotions with mandatory explanatory reason logging
- `apps/api/src/registry/router.py`: REST endpoints for lifecycle governance
  - `POST /api/v1/agents/{id_or_name}/promote`: Evaluate gates, advance agent stage, record immutable audit entry
  - `GET /api/v1/agents/{id_or_name}/history`: Query chronological stage transition audit history
  - `GET /api/v1/agents/{id_or_name}/gates/{target_stage}`: Dry-run preview endpoint for live UI checklists
- `apps/ui`: Complete Lifecycle Governance and Promotion UI
  - `/lifecycle`: Interactive 6-column Kanban board (`Draft`, `Prototype`, `Staging`, `Production`, `Deprecated`, `Retired`) with agent search, owner filters, and table/board view toggles
  - `PromoteModal`: Real-time gate verification checklist with pass/fail badges, operator affirmations (kill switch test, secrets revocation), rollback reason prompts, and disabled-state gating
  - `StageHistoryModal`: Immutable audit log modal displaying operator identity, timestamps, justifications, and expandable gate outcomes
  - `VersionDiffModal`: Side-by-side version comparison with summary badges (+ added, - removed, ~ modified, ! breaking), prominent breaking change alert panel, and field-level delta table
  - Full Vitest component suite with 23 passing tests and strict TypeScript verification (0 errors, 0 warnings)
- `docs/checkpoints/2026-10-15-phase-2-complete.md`: Phase 2 exit criteria verification and checkpoint sign-off
- Full suite passing: 214 Python tests (96% coverage) and 23 UI tests; clean bandit, pip-audit, and boundary checks



### Phase 1 — Walking Skeleton (Week 2-3)

#### Added
- `apps/ui`: Minimal Web UI dashboard (Next.js 16 App Router, TypeScript strict mode, Tailwind CSS v4, Lucide icons)
  - Agents Registry View (`/agents` and `/`): Dense table of registered AI employees, search and stage filters, stage badges (`Draft`, `Prototype`, `Staging`, `Production`, `Deprecated`, `Retired`), autonomy tags (`L0`-`L3`), and run triggers
  - Execution Runs View (`/runs`): Historical and active runs monitor with status badges, token usage, cost attribution, and trace view links
  - Trace Waterfall View (`/runs/[id]`): High-fidelity custom Gantt timeline displaying root `agent.run` and child `llm.call` spans with offset calculations, duration bars, and interactive span attribute inspection
  - Design system compliance: Non-blocking loading skeletons, empty state guides, error alerts with retry handlers, and zero hardcoded colors
  - Interactive Run Trigger Modal (`TriggerRunModal`): Form for testing and executing agent runs with JSON payload validation directly from the browser
  - API Integration: Added `CORSMiddleware` in `apps/api/src/main.py` and global `GET /api/v1/runs` endpoint in `runtime/router.py`
  - 17 Vitest unit and component tests passing cleanly
- `docs/adr/0009-minimal-ui-architecture-and-waterfall.md` — ADR documenting UI architecture, custom trace waterfall, and design system
- `packages/cli`: Varistha CLI developer workflow commands (`init`, `apply`, `run`)
  - Scaffolding (`varistha init [NAME]`): Interactive or flag-driven creation of canonical `agent.yaml` specifications compliant with `varistha-spec`
  - Declarative sync (`varistha apply -f <path>`): Offline local spec validation followed by idempotent API registration (`POST /api/v1/agents` or `POST /api/v1/agents/{id}/versions`)
  - Execution run (`varistha run <id-or-name>`): Trigger runs via API with polling watch mode spinner, USD cost attribution, token breakdowns, trace ID display, and machine-readable `--json` output
  - Rich terminal formatting with cross-platform CP1252/Windows console resilience
  - Decoupled HTTP client (`VaristhaClient`) communicating strictly via REST endpoints with zero internal API code imports
  - 37 unit and integration tests; 94% test coverage on `packages/cli`
- `docs/adr/0008-cli-architecture-and-workflow.md` — ADR documenting CLI architecture, client boundaries, offline validation, and watch mode polling
- `apps/api/src/observability` and `apps/api/src/shared/telemetry`: OpenTelemetry instrumentation, OTLP/HTTP receiver, and span persistence
  - OpenTelemetry semantic conventions (`conventions.py`): `varistha.*` attributes and GenAI conventions (`gen_ai.*`)
  - PII and secret redaction (`redaction.py`): Automatic sanitization of bearer tokens, API keys, passwords, and emails
  - OTLP/HTTP receiver endpoints (`router.py`): `POST /v1/traces` and `POST /api/v1/traces` supporting standard OTLP JSON export with Protobuf AnyValue decoding
  - Span persistence & queries: Storage in `spans` table, queried via `GET /api/v1/runs/{id}/spans` and `GET /api/v1/traces/{trace_id}`
  - Decoupled runtime tracing: In-process span recorder capturing `agent.run` root spans and `llm.call` child spans without cross-context import violations
  - 20 unit and integration tests across parser, telemetry, and router with 93% test coverage
- `docs/adr/0007-opentelemetry-instrumentation-and-otlp-receiver.md` — ADR documenting OpenTelemetry architecture, OTLP receiver, and span persistence
- `packages/spec`: Agent Spec Pydantic v2 models, YAML/dict validator, JSON Schema generator
  - Models: `AgentSpec`, `AgentMetadata`, `AgentSpecBody`, `ModelConfig`, `PluginRef`,
    `GuardrailsConfig`, `BudgetConfig`, `TriggerConfig`, `EvalConfig`
  - `validate_spec(raw: dict) -> AgentSpec` and `validate_spec_yaml(yaml: str) -> AgentSpec`
  - `SpecValidationError` with human-readable, location-prefixed error messages
  - `packages/spec/src/schema.json` — committed JSON Schema for editor tooling
  - `packages/spec/tests/fixtures/lead-researcher.yaml` — reference fixture from SPEC.md § 3.4
  - 25 unit tests; 84.5% coverage
- `docs/adr/0002-agent-spec-schema.md` — Pydantic v2 choice, `extra=forbid` policy,
  instructions-as-string rationale, autonomy Literal enum rationale
- New dependency: `email-validator>=2.1` (MIT) for `EmailStr` owner field validation
- `apps/api/src/shared/db`: SQLAlchemy 2.0 async database layer & Alembic migrations
  - ORM models: `Agent`, `AgentVersion`, `Run`, and `Span` with UUID primary keys, JSONB/JSON spec snapshots, cascading deletes, and `lazy="selectin"` async relationships
  - Database engine and session factory (`apps/api/src/shared/db/session.py`) with `get_db_session()` dependency generator
  - Application settings (`apps/api/src/shared/config.py`) via `pydantic-settings`
  - Alembic configuration (`apps/api/alembic.ini`, `apps/api/alembic/env.py`) supporting both async (`postgresql+asyncpg`, `sqlite+aiosqlite`) and sync database connections
  - Baseline migration `0001_initial_schema.py` creating `agents`, `agent_versions`, `runs`, and `spans` tables with indexes and constraints
  - 14 new unit and integration tests (7 model tests, 2 migration tests, 5 session tests) with 96% coverage
- `docs/adr/0003-database-schema-and-migrations.md` — ADR documenting database architecture, UUIDs, JSONB variants, selectin loading, and migration strategy
- New dev dependency: `aiosqlite>=0.20.0` (MIT) for fast in-memory async database testing
- `apps/api/src/registry`: REST API endpoints to register, list, get, and version agents
  - Pydantic response models (`schemas.py`): `AgentResponse`, `AgentDetailResponse`, `AgentListResponse`, `AgentVersionSummaryResponse`, `AgentVersionDetailResponse`, `ValidationErrorDetail`
  - Service layer (`service.py`): UUID/slug resolution, filtered pagination, spec validation via `packages/spec`, version immutability enforcement
  - Endpoints (`router.py`): `POST /api/v1/agents`, `GET /api/v1/agents`, `GET /api/v1/agents/{id_or_name}`, `GET /api/v1/agents/{id_or_name}/versions`, `GET /api/v1/agents/{id_or_name}/versions/{version}`, `POST /api/v1/agents/{id_or_name}/versions`
  - Coverage & concurrency: Configured `greenlet` and `thread` concurrency in `pyproject.toml`
  - 13 integration tests (`test_router.py`) with 100% test coverage on `registry/` modules
- `docs/adr/0004-registry-api-design.md` — ADR documenting registry API routes, immutability rules, and service layer architecture
- `apps/api/src/runtime`: Runtime Protocol, LangGraph single-prompt adapter, and run execution endpoints
  - `Runtime` protocol & dataclasses (`interface.py`): `@runtime_checkable Protocol`, `RunContext`, `RunResult`
  - LangGraph adapter (`adapter.py`): `StateGraph` compiled single-prompt workflow invoking LiteLLM, calculating tokens and cost, with JSON parsing and exception handling
  - Mock runtime (`mock.py`): Deterministic, offline execution engine supporting failure injection and approval-waiting states
  - Schemas (`schemas.py`): `RunCreateRequest`, `RunResponse`, `RunListResponse`
  - Service layer (`service.py`): `trigger_agent_run()`, `get_run()`, `list_runs_for_agent()` with lifecycle status updates (`running` -> `completed` / `failed`)
  - Endpoints (`router.py`): `POST /api/v1/agents/{id_or_name}/runs`, `GET /api/v1/agents/{id_or_name}/runs`, `GET /api/v1/runs/{id}`
  - 15 unit and integration tests with 97% overall coverage on `runtime/`
- `docs/adr/0005-runtime-interface-and-langgraph-adapter.md` — ADR documenting runtime decoupling, LangGraph encapsulation, LiteLLM usage, and mock runtime strategy
- New dependency: `langgraph>=0.2.0` (MIT, added to `varistha-api`)
- `apps/api/src/plugins` and `plugins/web-fetch`: MCP Plugin Host and web-fetch plugin with SSRF protection
  - Plugin manifest validation (`manifest.py`): Pydantic model enforcing `name`, `version`, `entrypoint`, `scopes`, `risk` level, and `untrusted_output` flag
  - Plugin host (`host.py`): Plugin discovery across filesystem directories, tool schema inspection, and permission gating outside the model (`is_plugin_enabled`)
  - Web fetch plugin (`plugins/web-fetch`): Async HTTP fetcher (`fetcher.py`) with HTML text extraction, `<title>` extraction, script/style sanitization, and redirect safety
  - SSRF protection (`ssrf.py`): Strict IPv4/IPv6 validation blocking loopback (`127.0.0.0/8`, `::1`), RFC 1918 private ranges, cloud metadata endpoints (`169.254.169.254`), CGNAT (`100.64.0.0/10`), non-HTTP schemes, and credentials in URLs
  - Untrusted output tagging: Web responses explicitly flagged with `untrusted: True`
  - 37 unit tests across host, SSRF, and fetcher modules with 98% overall test coverage
- `docs/adr/0006-mcp-plugin-host-and-ssrf-protection.md` — ADR documenting plugin architecture, security boundaries, and SSRF defense-in-depth

### Phase 0 — Foundations (Week 1)


#### Added
- Monorepo structure: `apps/api`, `apps/worker`, `apps/ui`, `packages/cli`, `packages/spec`, `packages/sdk`, `plugins/`, `role-packs/`, `docs/`, `deploy/`
- Python workspace with `uv`: FastAPI placeholder with `/health` and `/` endpoints
- `pyproject.toml` with ruff (full lint suite), pyright strict, pytest, bandit, pip-audit
- Two passing smoke tests for health and root endpoints
- `AGENTS.md` and `GEMINI.md` — agent instructions for AI-assisted development
- `LICENSE` (Apache-2.0), `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- `CHANGELOG.md` (this file)
- `docs/SPEC.md` — product specification
- `docs/adr/0001-monorepo-and-stack.md` — ADR for monorepo and stack decisions
- `.github/workflows/ci.yml` — CI pipeline (lint, type-check, test)
- `.github/workflows/code-review.yml` — automated code review pipeline
- `deploy/docker-compose.yml` — Postgres, API and UI placeholders
- `deploy/.env.example` — documented environment variables
- `scripts/check_boundaries.py` — architecture boundary enforcement

[Unreleased]: https://github.com/SSRINIBASS/varistha/compare/HEAD...HEAD
