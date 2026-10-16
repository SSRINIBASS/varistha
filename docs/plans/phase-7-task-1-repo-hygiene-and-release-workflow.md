# Plan: Phase 7 Task 1 — Repo Hygiene, Release Packaging Workflow & Flagship README

## Objective
Establish complete repository hygiene, release automation, and a flagship `README.md` landing page for Varistha v0.1.0 launch as specified in `docs/SPEC.md § 6`.

## Scope of Changes
1. **Flagship `README.md`**:
   - Modern badges (License Apache-2.0, Python 3.12, Next.js, OTel, CI status).
   - Clear value proposition: Open-source, self-hostable control plane to build, run, monitor and govern AI agents (AI employees) for startups.
   - ASCII architecture diagram showing Core (API, Worker, Postgres+pgvector), OTel, Plugins (MCP), UI, and LiteLLM.
   - Key Capabilities: Declarative Specs, Lifecycle Gates, Human-in-the-Loop Approvals Inbox, Policy Engine & Guardrails, OpenTelemetry Observability, Built-in Role Packs & MCP Plugins.
   - 5-Minute Quickstart guide with Docker Compose.
   - CLI quickstart (`varistha init`, `varistha apply`, `varistha run`).
   - UI Showcase & Screenshots links.
   - Security, Roadmap & Contributing links.

2. **Repository Hygiene & Templates**:
   - Update `CONTRIBUTING.md` with guidelines on PRs, testing requirements (≥80% coverage), boundaries script, commit conventions, and architecture principles.
   - Update `SECURITY.md` with full security disclosures, vulnerability reporting, and automated security safeguards.
   - Add `.github/ISSUE_TEMPLATE/plugin_proposal.yml` for community MCP plugin proposals.
   - Update `.github/pull_request_template.md` with checklist for license, tests, ruff, pyright, and boundaries.

3. **Release Automation (`.github/workflows/release.yml`)**:
   - Trigger on pushed tags `v*`.
   - Job 1: Build & test verification gate.
   - Job 2: Build & push multi-arch Docker images to GitHub Container Registry (GHCR): `ghcr.io/ssrinibass/varistha-api`, `ghcr.io/ssrinibass/varistha-worker`, `ghcr.io/ssrinibass/varistha-ui`.
   - Job 3: Build Python wheel distributions for `varistha-cli`, `varistha-spec`, `varistha-sdk`.

4. **Testing**:
   - Add unit test `apps/api/src/shared/tests/test_repo_hygiene.py` verifying license compliance, presence of required docs, issue templates validity, and README consistency.

## Verification
- `python scripts/check_boundaries.py`
- `uv run ruff check .`
- `uv run pyright apps/api`
- `uv run pytest apps/api/src/shared/tests/test_repo_hygiene.py`
- Git commit & push to `master` and `main` with green GitHub Actions.
