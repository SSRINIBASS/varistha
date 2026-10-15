# Guide: Development Workflow & Tooling

## 1. Monorepo Structure

Varistha uses a hybrid monorepo:
- **Backend & Python packages**: Managed with `uv` (`apps/api`, `apps/worker`, `packages/cli`, `packages/spec`, `packages/sdk`).
- **Frontend**: Next.js with `pnpm` (`apps/ui`).
- **Deployment**: `deploy/docker-compose.yml` and `deploy/.env.example`.

```
varistha/
├── apps/
│   ├── api/          # FastAPI control plane API
│   ├── worker/       # LangGraph agent runtime worker
│   └── ui/           # Next.js 15 + shadcn/ui dashboard
├── packages/
│   ├── spec/         # Declarative AgentSpec models, schema & validator
│   ├── sdk/          # Python SDK for programmatic control
│   └── cli/          # varistha CLI
├── docs/             # Architecture, ADRs, checkpoints, and guides
├── deploy/           # Docker Compose and environment configs
└── scripts/          # Architecture boundary check and helper scripts
```

---

## 2. Python Environment Setup (`uv`)

Install dependencies across all workspace packages:
```bash
uv sync --all-packages
```

Run test suite with coverage:
```bash
uv run pytest --cov=apps/api/src/shared --cov=packages/spec/src --cov-fail-under=80
```

Run lint and formatting:
```bash
uv run ruff check .
uv run ruff format --check .
```

Auto-fix lint and formatting:
```bash
uv run ruff check . --fix
uv run ruff format .
```

Type checking (Pyright strict):
```bash
uv run pyright apps/ packages/
```

Verify architecture boundaries:
```bash
uv run python scripts/check_boundaries.py
```

---

## 3. UI Environment Setup (`pnpm`)

Run UI unit/smoke tests:
```bash
cd apps/ui
pnpm install
pnpm test
```

---

## 4. TDD Cycle (Red -> Green -> Refactor)

1. **Red**: Write a failing unit or integration test defining expected behavior.
2. **Green**: Write the minimal code required to make the test pass.
3. **Refactor**: Clean up the code while keeping tests green, running linters and type checks.
4. **Gate**: Verify test coverage remains ≥ 80% for the modified module.

---

## 5. Git Commit Convention

```
<type>(<scope>): <description>
```

- **Types**: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`, `security`
- **Scopes**: `registry`, `runtime`, `governance`, `observability`, `identity`, `plugins`, `cli`, `ui`, `deploy`
