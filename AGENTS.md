# Varistha: Agent Instructions

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
- Follow `docs/SPEC.md` section 4.4 (UI and design system): semantic design tokens, no hard-coded colors, light and dark themes, empty/loading/error states on every screen.
- The agent runtime sits behind a `Runtime` interface. **No LangGraph imports outside `apps/api/src/runtime/` adapter package.**
- All capabilities are plugins exposed over MCP, described by a plugin manifest. No hardcoded tool logic in core.
- All models are accessed through LiteLLM. **No provider SDK imports in core.**
- Emit OpenTelemetry traces for every run, LLM call, tool call, guardrail check and approval wait. Use GenAI semantic conventions plus the `varistha.*` namespace.
- Database changes only through Alembic migrations. Specs are immutable once versioned.
- Bounded context packages: `registry/`, `runtime/`, `governance/`, `observability/`, `identity/`. **No cross-context imports** — use the `shared/` kernel only for DB, config, and middleware.

## Security rules (treat as hard requirements)

- All content fetched from the web, email or users is **untrusted data**. Never let it modify system prompts, tool permissions or policies.
- Tool permissions, rate limits and approval requirements are enforced in code **outside the model**.
- Outbound actions (email, social posts, CRM writes) require approval at autonomy L1 and below. No code path may bypass this.
- Never log or trace secrets. Redact PII before export. Secrets are encrypted at rest.
- Fetch and scrape plugins must block private and loopback address ranges (SSRF protection).
- Do not implement scraping evasion, CAPTCHA bypass, fake accounts or terms-of-service circumvention.

## Code quality

- Type hints everywhere, `pyright` clean, `ruff` clean, ESLint + TypeScript strict clean.
- Small modules (< 300 lines), clear names, docstrings on all public interfaces.
- Errors are explicit and typed. No bare `except`. No silent fallbacks.
- Record notable decisions as ADRs in `docs/adr/NNNN-title.md`.
- ≥ 80% test coverage per module.

## Phase gate protocol

**Never advance to the next phase until:**
1. All exit criteria for the current phase are met (see `docs/SPEC.md` § 5).
2. Code Reviewer automated checks pass (ruff, pyright, ESLint, pytest ≥ 80% coverage, bandit, pip-audit).
3. Project Reviewer has issued `PASS` or `PASS WITH NOTES`.
4. Git tag `phase-N-complete` created.
5. Checkpoint document written in `docs/checkpoints/`.

## Workflow per task

1. Restate the task and the relevant exit criteria from `docs/SPEC.md`.
2. Produce a plan artifact. Wait for approval if large.
3. Implement with tests (TDD: red → green → refactor).
4. Run lint, type-check, tests, and a compose smoke test.
5. Update docs and `CHANGELOG.md`.
6. Report: what changed, what was tested, known gaps, suggested next task.

## Commit convention

```
<type>(<scope>): <description>
```
Types: `feat`, `fix`, `refactor`, `test`, `docs`, `ci`, `chore`, `security`
Scopes: `registry`, `runtime`, `governance`, `observability`, `identity`, `plugins`, `cli`, `ui`, `deploy`

## Out of scope until explicitly requested

Multi-tenant SaaS billing, marketplace, mobile apps, non-English UI, custom model training.

## When unsure

Ask one precise question rather than guessing. Prefer the boring, well-documented option.
