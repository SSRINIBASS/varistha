# Changelog

All notable changes to Varistha will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 1 — Walking Skeleton (Week 2-3)

#### Added
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

[Unreleased]: https://github.com/your-org/varistha/compare/HEAD...HEAD
