# Contributing to Varistha

Thank you for your interest in contributing to Varistha! Varistha is an open-source, self-hostable control plane to build, run, monitor and govern AI agents for startups.

The project is licensed under the [Apache License, Version 2.0](LICENSE).

---

## Architecture Principles

1. **Bounded Contexts**: Code is organized into strict domains:
   - `registry/`: Agent specifications, versions, lifecycle stages, and transitions.
   - `runtime/`: Execution engine, LangGraph adapters, triggers, and state persistence.
   - `governance/`: Human approvals, guardrail middleware, policies, and budgets.
   - `observability/`: OpenTelemetry spans, metrics, and trace queries.
   - `identity/`: RBAC, API keys, and encrypted secrets vault.
   - **Cross-context imports are forbidden.** Only import shared database models and configuration via `shared/`.
2. **Outside-the-Model Enforcement**: Approvals, tool permissions, rate limits, and budgets must be enforced in deterministic Python code, never delegated to model prompts.
3. **OSI-Approved Dependencies Only**: All core dependencies must be licensed under OSI-approved licenses (Apache-2.0, MIT, BSD). Restricted or AGPL tools may only exist as optional plugins.
4. **Small Modules**: Maintain files under 300 lines with explicit typed errors and complete type annotations.

---

## Development Setup

### 1. Prerequisites
- Python 3.12+
- Node.js 20+ and `pnpm`
- Docker and Docker Compose
- `uv` package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### 2. Initial Setup
```bash
# Clone the repository
git clone https://github.com/SSRINIBASS/varistha.git
cd varistha

# Copy environment variables
cp deploy/.env.example deploy/.env

# Sync Python packages
uv sync --all-packages

# Install frontend dependencies
cd apps/ui && pnpm install && cd ../..
```

### 3. Local Development Services
```bash
# Start PostgreSQL database with pgvector
docker compose -f deploy/docker-compose.yml up -d postgres

# Run database migrations
uv run alembic upgrade head

# Start API service
uv run --package varistha-api uvicorn apps.api.src.main:app --reload --port 8000

# Start UI development server
cd apps/ui && pnpm dev
```

---

## Pre-Pull Request Checklist

Before submitting a pull request, ensure all verification gates pass locally:

1. **Architecture Boundaries Check**:
   ```bash
   python scripts/check_boundaries.py
   ```
2. **Linting & Formatting**:
   ```bash
   uv run ruff check .
   uv run ruff format --check .
   ```
3. **Static Type Checking**:
   ```bash
   uv run pyright apps/api
   ```
4. **Test Suite & Coverage** (Coverage must be ≥ 80% per module):
   ```bash
   uv run pytest -q --cov=apps/api/src
   ```
5. **Security Scanning**:
   ```bash
   uv run bandit -ll -r apps/api/src
   uv run pip-audit
   ```
6. **Frontend Checks**:
   ```bash
   cd apps/ui && pnpm lint && pnpm tsc --noEmit && pnpm test && cd ../..
   ```

---

## Commit Convention

Commit messages follow conventional commits:
```
<type>(<scope>): <description>
```

- **Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`, `security`
- **Scopes**: `registry`, `runtime`, `governance`, `observability`, `identity`, `plugins`, `cli`, `ui`, `deploy`

Examples:
- `feat(governance): implement side-by-side diff view in approvals modal`
- `fix(runtime): prevent race condition during concurrent sqlite refreshes`
- `test(identity): add unit tests for aes-256-gcm secrets vault`

---

## Security Vulnerabilities

Please do **NOT** file public GitHub issues for security vulnerabilities. Review our [SECURITY.md](SECURITY.md) for reporting procedures or email **security@varistha.dev**.
