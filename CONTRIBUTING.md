# Contributing to Varistha

Thank you for your interest in contributing! Varistha is licensed under Apache-2.0.

## Quick start

1. Fork the repo and clone it
2. Copy `deploy/.env.example` to `deploy/.env`
3. `docker compose -f deploy/docker-compose.yml up -d`
4. `uv sync --all-packages` (Python)
5. `pnpm install` in `apps/ui/`

## Before you open a PR

- Run `uv run ruff check .` and `uv run ruff format --check .`
- Run `uv run pyright`
- Run `uv run pytest --cov` (must stay ≥ 80% coverage)
- Run `pnpm lint` and `pnpm tsc --noEmit` in `apps/ui/`
- Every new feature needs unit tests and (for API routes) integration tests

## Commit convention

```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`, `security`

## License requirements

Only OSI-approved licenses in core. AGPL or restricted tools only as optional plugins. Always state the license of any new dependency in the PR.

## Code of conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security issues

See [SECURITY.md](SECURITY.md) — please do **not** open a public issue for security vulnerabilities.
