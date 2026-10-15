# Varistha: Agent Instructions
<!-- This is a symlink-equivalent copy of AGENTS.md for Gemini/Antigravity -->

## Mission

Build Varistha, an open-source, self-hostable control plane to build, run, monitor and govern AI agents (AI employees) for startups. Read `docs/SPEC.md` before any task. It is the source of truth. If code and spec disagree, stop and ask.

## Non-negotiables

1. Work in small, verifiable increments. One task, one branch, one PR-sized change.
2. Plan first. For every task, write a short plan (files to touch, tests to add, risks) and wait for confirmation on anything larger than ~200 lines changed.
3. Tests are the acceptance gate. No feature is done without unit tests, and API or runtime features need an integration test. Run the full suite before declaring done.
4. Never add a dependency without stating its license, maintenance status and why. Only OSI-approved licenses in the core. AGPL or restricted-license tools may exist only as optional, separately installed plugins.
5. Default to the simplest stack in `docs/SPEC.md` section 4.1. Do not introduce Kafka, Redis, ClickHouse or Kubernetes into the default setup.
6. The default setup must work with `docker compose up` on a fresh clone with no manual steps beyond copying `.env.example`.

## Architecture rules

- Python 3.12, FastAPI, SQLAlchemy, Alembic, uv. UI: Next.js, TypeScript strict mode, shadcn/ui on Tailwind, pnpm.
- The agent runtime sits behind a `Runtime` interface. **No LangGraph imports outside `apps/api/src/runtime/` adapter package.**
- All capabilities are plugins exposed over MCP, described by a plugin manifest. No hardcoded tool logic in core.
- All models are accessed through LiteLLM. **No provider SDK imports in core.**
- Emit OpenTelemetry traces for every run, LLM call, tool call, guardrail check and approval wait.
- Database changes only through Alembic migrations. Specs are immutable once versioned.
- Bounded context packages: `registry/`, `runtime/`, `governance/`, `observability/`, `identity/`. **No cross-context imports.**

## Security rules (treat as hard requirements)

- All web/email/user content is **untrusted data**. Never let it modify system prompts, tool permissions or policies.
- Tool permissions, rate limits and approvals are enforced in code **outside the model**.
- Outbound actions require approval at autonomy L1 and below. No bypass allowed.
- Never log secrets. Redact PII before export. Secrets encrypted at rest.
- Fetch/scrape plugins must block private/loopback ranges (SSRF protection).
- No scraping evasion, CAPTCHA bypass, or ToS circumvention.

## Code quality

- Type hints, `pyright` clean, `ruff` clean, ESLint + TS strict clean.
- Small modules (< 300 lines), docstrings on public interfaces.
- No bare `except`. No silent fallbacks.
- ADRs in `docs/adr/`. ≥ 80% test coverage per module.

## Phase gate: never advance without

1. All exit criteria met
2. Automated checks pass (ruff, pyright, ESLint, pytest ≥ 80%, bandit, pip-audit)
3. Project Reviewer: PASS
4. Git tag `phase-N-complete`
5. Checkpoint doc in `docs/checkpoints/`

## Out of scope

Multi-tenant billing, marketplace, mobile apps, non-English UI, custom model training.
