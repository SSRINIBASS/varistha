# ADR-0001: Monorepo Layout and Stack Decisions

**Date:** 2026-10-15
**Status:** Accepted
**Deciders:** Varistha core team

---

## Context

We are building Varistha from scratch. Before writing any feature code, we need to commit to a monorepo layout, toolchain, and stack so all subsequent decisions are consistent.

## Decision

### Monorepo layout

```
apps/api/       — Python FastAPI control plane
apps/worker/    — Python background worker
apps/ui/        — Next.js frontend
packages/cli/   — varistha CLI (Python)
packages/spec/  — Agent spec schema + validators (shared Python)
packages/sdk/   — Plugin author SDK (Python)
plugins/        — Built-in MCP plugins
role-packs/     — Installable agent role packs
docs/           — SPEC.md, ADRs, guides, plans, checkpoints
deploy/         — Docker Compose, .env.example
scripts/        — Boundary checker, CI helpers
```

### Python toolchain
- **uv** for workspace + dependency management (Apache-2.0, extremely fast)
- **ruff** for linting + formatting (MIT, replaces flake8/isort/black)
- **pyright** strict for type checking (MIT)
- **pytest** + pytest-asyncio + pytest-cov for tests
- **bandit** for security scanning
- **pip-audit** for dependency vulnerability scanning

### Frontend toolchain
- **pnpm** workspaces for Node.js package management
- **Next.js 16** (App Router) + **TypeScript strict mode**
- **shadcn/ui** on **Tailwind CSS** for components (no Material UI — rationale in SPEC.md §4.4)
- **vitest** for unit + component tests
- **ESLint** with next/core-web-vitals config

### Backend stack (core)
- **Python 3.12**, **FastAPI** (MIT), **SQLAlchemy 2** async (MIT), **Alembic** (MIT)
- **PostgreSQL 16** + pgvector — single DB for all state
- **Procrastinate** (Apache-2.0) for Postgres-backed job queuing (no Redis in default setup)
- **LiteLLM** (MIT) — unified gateway to any model provider or local Ollama/vLLM
- **LangGraph** (MIT) behind a `Runtime` interface adapter — can be swapped without core changes
- **OpenTelemetry SDK** (Apache-2.0) with OpenInference instrumentation

### Deployment
- **Docker Compose** as default (4 containers: postgres, api, worker, ui)
- Observability stack (Langfuse, Grafana) is an optional `--profile observability` override
- Helm chart deferred to post-launch

## Consequences

- All Python in the monorepo shares one virtual environment via `uv sync --all-packages`
- UI has its own `node_modules` managed by pnpm
- The `Runtime` interface in `apps/api/src/runtime/adapter.py` is the seam for future framework swaps
- LangGraph is only imported inside `apps/api/src/runtime/langgraph_adapter.py`
- No cross-context imports between bounded contexts (registry, runtime, governance, observability, identity)
- Architecture boundary violations caught by `scripts/check_boundaries.py` in CI

## Alternatives considered

- TypeScript for the core: rejected because the eval/ML ecosystem (Ragas, DeepEval, Guardrails AI, Presidio) is Python-native
- Hono instead of FastAPI: rejected because FastAPI's OpenAPI generation and async support is mature
- Redis for queuing: rejected to keep default `docker compose up` at 4 containers
- Material UI: rejected per SPEC.md §4.4 — Emotion + server components friction, paid Data Grid features
