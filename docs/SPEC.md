# Varistha: Ideation, Critique, Plan and Antigravity Handoff

*Open-source meta agent harness to build, monitor, govern and ship AI employees for startups. Prepared October 2026.*

## 1. The idea, sharpened

**One-liner:** Varistha is a self-hostable control plane where a startup installs AI employees as role packs, then runs them under real operational discipline: a registry, lifecycle stages, observability, evals, guardrails and human approvals.

**Three pillars**

1. **Build:** declarative agent spec, role packs, plugins that toggle on and off per agent.
2. **Run:** durable runtime, triggers (schedule, webhook, manual), approval inbox, budgets, kill switch.
3. **Govern (AgentOps):** traces, evals, feedback, confidence signals, guardrails, lifecycle promotion.

**The wedge (what makes it not just another agent builder):** every agent is treated like an employee. It has an owner, a stage, an autonomy level and promotion gates backed by eval scores and human-feedback data. Tools like Dify, n8n and Flowise build agents. Langfuse and Phoenix observe them. Few open-source projects tie build, run and govern into one opinionated, startup-ready lifecycle. Verify this landscape yourself before committing, because the space moves fast.

**Target user:** 1 to 20 person startups and solo agencies with no ML platform team and no patience for a 12-container setup.

## 2. Critique (honest)

1. **Scope explosion is the number one killer.** Builder + registry + AgentOps + scraping + social posting + role packs is five products. A solo builder who attempts all at once ships none. *Fix:* build one vertical slice end to end first (Lead Research agent), then widen.
2. **Do not rebuild observability.** Emit standard OpenTelemetry (GenAI semantic conventions, still evolving) and let users fan out to Langfuse, Grafana, SigNoz or anything else. Build only the thin UI layer that is agent-specific (runs, approvals, lifecycle).
3. **Heavy default stack kills easy setup.** Self-hosting Langfuse alone needs ClickHouse, Redis and object storage. *Fix:* the default is `docker compose up` with 4 containers (api, worker, ui, postgres). Heavy observability is an optional compose profile.
4. **LinkedIn and X automation is a legal and account-ban minefield.** Scraping LinkedIn violates its terms and gets accounts banned. X's API is paid and rate limited. Cold email touches CAN-SPAM, GDPR and India's DPDP Act. *Fix:* social and outbound plugins ship with approval-required defaults, rate limits, an opt-out/suppression list, and a documented compliance note. Prefer official APIs and user-supplied credentials. Varistha should not provide scraping evasion.
5. **Prompt injection through scraped content is your biggest security risk.** An agent that reads the web and can also send emails or post is the classic exfiltration setup. *Fix:* treat all fetched content as untrusted data, enforce tool-level permissions outside the model, require approval for outbound actions, and separate read-only agents from acting agents.
6. **The employee framing over-promises.** Autonomous agents are not reliable enough yet to be trusted unattended. *Fix:* make autonomy a dial (L0 to L3, see below) and make earning autonomy the core product idea. This turns a weakness into your differentiator.
7. **Model-reported confidence is poorly calibrated.** Do not ship a confidence score that is just the LLM saying 0.9. *Fix:* compute confidence from verifiable signals: schema validation, citation or grounding checks, a separate verifier or judge model, agreement across samples on high-stakes steps, and historical approval rate for similar tasks. Label it a review-priority score, not a probability.
8. **LLM-as-judge evals are noisy.** Calibrate judges against a small human-labelled set per agent, pin judge model versions, and prefer deterministic checks wherever possible.
9. **Licensing traps.** Some popular pieces are not OSI open source (for example n8n's fair-code license and Phoenix's Elastic License 2.0), and some are AGPL (for example Firecrawl). Check each dependency. Keep the core Apache-2.0 and keep optional AGPL or restricted tools as separate, user-installed plugins.
10. **Framework churn.** Agent frameworks change monthly. Put the runtime behind your own adapter interface so you can swap LangGraph for something else without rewriting the product.
11. **Positioning risk.** Lindy, Relevance AI, CrewAI, Dify and others overlap partially. You win on self-hosting, lifecycle governance, role packs and startup ergonomics, not on feature count.
12. **Name.** Varistha is distinctive. Check domain, GitHub org, PyPI and npm availability before you build the brand.

**Verdict:** a strong idea if scoped as *the open-source AgentOps and lifecycle layer with installable role packs*, and weak if scoped as *a universal agent platform*. Build the first.

## 3. Product definition

### 3.1 Core concepts

- **Agent Spec:** a versioned, declarative YAML file describing role, model, instructions, plugins, guardrails, eval suite, triggers, budget and autonomy.
- **Role Pack:** a bundle of agent specs, prompts, eval datasets and plugin requirements for one job (for example Lead Research).
- **Plugin:** a capability exposed through MCP (Model Context Protocol), such as web scrape, email, CRM, LinkedIn or X. It has a manifest declaring scopes, risk level and whether approval is required.
- **Run:** one execution of an agent, with a trace, cost, outputs and status.
- **Approval:** a human decision on a proposed action, with an optional edit. The diff between proposed and final is your best feedback signal.
- **Policy:** guardrail rules applied to input, output and tool calls.

### 3.2 Lifecycle stages

Draft, Prototype, Staging, Production, Deprecated, Retired.

| Transition | Gate |
| --- | --- |
| Draft to Prototype | Spec validates, runs once successfully |
| Prototype to Staging | Eval suite exists and passes threshold, guardrails attached, owner assigned |
| Staging to Production | Eval score above threshold on current version, N reviewed runs with acceptable approval rate, budget set, kill switch tested |
| Production to Deprecated | Replacement named, traffic drained |
| Deprecated to Retired | Triggers disabled, history kept, secrets revoked |

Every transition is written to an immutable audit log.

### 3.3 Autonomy levels

- **L0 Suggest:** the agent proposes, a human acts.
- **L1 Act with approval:** the agent acts only after human approval (default for all outbound actions).
- **L2 Act with sampled review:** the agent acts, and a percentage of actions are reviewed after the fact.
- **L3 Autonomous within budget:** the agent acts freely within cost, rate and scope limits.

Promotion between levels is gated by eval and feedback data, never by a toggle alone.

### 3.4 Example agent spec

```yaml
apiVersion: varistha/v1
kind: Agent
metadata:
  name: lead-researcher
  owner: founder@example.com
  stage: prototype
  version: 0.3.0
spec:
  role: Find and qualify B2B leads matching our ICP, draft a personalised first touch.
  model:
    primary: gpt-class-or-any-litellm-id
    fallback: local/ollama-model
  instructions: ./prompts/lead-researcher.md
  plugins:
    - name: web-fetch
      enabled: true
    - name: web-search
      enabled: true
    - name: email-draft
      enabled: true
    - name: email-send
      enabled: false
    - name: linkedin-post
      enabled: false
  autonomy: L1
  guardrails:
    input: [pii-redact, injection-scan]
    output: [schema-valid, no-unverified-claims]
    tools: [outbound-needs-approval, rate-limit-50-per-day]
  budget:
    max_usd_per_run: 0.50
    max_usd_per_day: 10
  triggers:
    - type: schedule
      cron: 0 9 * * 1-5
    - type: manual
  evals:
    suite: ./evals/lead-researcher.yaml
    min_pass_rate: 0.85
```

### 3.5 Plugin manifest

```yaml
name: web-fetch
transport: mcp-stdio
command: python -m varistha_plugins.web_fetch
risk: low
scopes: [network:read]
requires_approval: false
untrusted_output: true
config_schema: ./config.schema.json
```

Plugins that return web or user-generated content must set `untrusted_output: true`, which makes the runtime wrap that content as data and apply injection scanning.

### 3.6 Role packs

- **v1:** Lead Research, Competitor Intelligence.
- **v2:** Content and Marketing (draft posts, repurpose), Outbound Client Acquisition (sequences, follow-ups, always approval-gated), Customer Support Triage.
- **Later:** Investor Update, Recruiting Screen, Market Monitor.

## 4. Architecture

```
                    +-------------------+
                    |   Web UI (Next.js)|
                    +---------+---------+
                              |
+----------+   REST/SSE  +----v--------------------+
|  CLI     +------------>|  Control Plane API      |
| varistha |             |  (FastAPI)              |
+----------+             |  registry, lifecycle,   |
                         |  approvals, policies,   |
                         |  OTLP receiver, evals   |
                         +----+-----------+--------+
                              |           |
                      +-------v--+   +----v------------------+
                      | Postgres |   |  Worker(s)            |
                      | +pgvector|   |  Runtime adapter      |
                      +----------+   |  (LangGraph first)    |
                                     |  guardrail middleware |
                                     +----+-------------+----+
                                          |             |
                                  +-------v--+     +----v-------+
                                  | LiteLLM  |     | MCP plugins|
                                  | (models) |     | scrape,... |
                                  +----------+     +------------+

   OTel SDK in worker --> OTLP --> Varistha (built-in)  and/or
   OTel Collector --> Langfuse / Grafana / SigNoz (optional profile)
```

### 4.1 Stack decisions

| Concern | Pick | Alternatives |
| --- | --- | --- |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic | TypeScript with Hono |
| Database | PostgreSQL 16 plus pgvector | none needed early |
| Queue | Postgres-backed queue (Procrastinate) | Temporal or Hatchet later via adapter |
| Agent runtime | LangGraph behind a `Runtime` interface (checkpointing and human interrupts built in) | OpenAI Agents SDK, Pydantic AI, Google ADK |
| Model gateway | LiteLLM (any provider, local via Ollama or vLLM) | direct SDKs |
| Tool protocol | MCP | native Python tools as a fallback |
| Telemetry | OpenTelemetry SDK, OpenLLMetry or OpenInference instrumentation, GenAI semantic conventions | custom spans |
| Trace backends | built-in Postgres store by default | Langfuse, Grafana Tempo, SigNoz via Collector |
| Evals | promptfoo-style YAML suites run by Varistha, plus Ragas or DeepEval as optional | Inspect |
| Guardrails | Guardrails AI, Presidio (PII), LLM Guard, NeMo Guardrails as pluggable policy engines | custom rules |
| Scraping | Playwright and Crawl4AI (Apache-2.0) as default plugins | Firecrawl (AGPL, optional), browser-use |
| Auth | Better Auth or Zitadel | Keycloak |
| Secrets | encrypted in Postgres for v0, OpenBao or Infisical adapter later | env vars |
| UI | Next.js, shadcn/ui (Radix and Tailwind), TanStack Table and Query, Recharts, React Flow, dnd-kit | Mantine (closest runner-up), Material UI, SvelteKit |
| Packaging | Docker Compose first, Helm chart later | none |
| Monorepo | uv (Python) and pnpm (UI) workspaces | Nx |

### 4.2 Core data model

`agents`, `agent_versions` (immutable spec snapshots), `stage_transitions` (audit), `plugins`, `agent_plugins`, `runs`, `spans` (OTLP-derived), `approvals`, `feedback`, `eval_suites`, `eval_runs`, `eval_results`, `policies`, `policy_events`, `budgets`, `secrets`, `api_keys`, `audit_log`.

### 4.3 Telemetry conventions

One trace per run. Spans for each LLM call, tool call, guardrail check and approval wait. Attributes follow the OpenTelemetry GenAI conventions where they exist and use a `varistha.*` namespace for agent id, version, stage, autonomy level, run cost and approval outcome. Never log secrets, and redact PII before export.

### 4.4 UI and design system

Use shadcn/ui on Tailwind rather than Material UI: it gives a clean, dense, neutral look that suits an operations dashboard, and you own the component code. Material UI's free core is solid, but its advanced Data Grid features (row grouping, tree data and similar) sit in paid Pro and Premium tiers, which clashes with an Apache-2.0 project. Its Emotion styling also needs extra setup with Next.js server components, and the Material look is hard to make compact. Mantine is the closest runner-up if you want more components out of the box with less assembly.

| Need | Library |
| --- | --- |
| Base components, forms, dialogs, command palette | shadcn/ui (Radix primitives) with Tailwind, cmdk |
| Dense tables for agents, runs and approvals | TanStack Table |
| Cost, latency and eval-trend charts | Recharts through shadcn charts |
| Lifecycle board (agents by stage) | dnd-kit |
| Trace waterfall | Custom component, since spans are time bars and no library fits |
| Workflow and dependency graph | React Flow (xyflow) |
| Agent spec editor | CodeMirror 6 with YAML and JSON Schema validation |
| Diffs (spec versions, approval edits) | CodeMirror merge view |
| Icons | lucide-react |

**Design rules**

- **One question per screen.** Registry answers what exists and at which stage. Runs answers what happened. Approvals answers what needs me. Evals answers whether it is improving. Cost answers what it is spending.
- **Semantic status colors, used the same way everywhere.** Stage badges: Draft grey, Prototype blue, Staging violet, Production green, Deprecated amber, Retired slate. Risk tags: Green, Amber, Red. Always pair color with an icon or label, never color alone.
- **Dense but calm.** 14px base text, 36px table rows, one primary action per screen, generous whitespace between sections rather than borders.
- **Show diffs, not blobs.** An approval shows the proposed output next to the human edit. A version change shows a spec diff.
- **Keyboard first.** A command palette for navigation and actions, and j/k navigation with approve and reject shortcuts in the approvals inbox.
- **Every screen has empty, loading and error states.** An empty registry teaches the first step, for example installing a role pack.
- **Light and dark themes** from CSS variable tokens, with WCAG AA contrast.
- **Visual information over text.** Sparklines in agent rows, a cost bar against budget, a run timeline that shows where time and tokens went, and an eval score trend per version.

## 5. Execution order

Each phase has exit criteria. Do not start the next phase until they are met. Timelines assume one developer working with Antigravity agents, so treat them as rough.

**Phase 0: Foundations (week 1)** Monorepo, license (Apache-2.0), CI (lint, type-check, tests), `docker compose up` bringing up postgres, api and ui placeholders, ADR folder, AGENTS.md in place. *Exit:* CI green, compose starts clean from a fresh clone.

**Phase 1: Walking skeleton (weeks 2 to 3)** Agent Spec schema and validator. API to create and read agents. Worker runs one agent through the LangGraph adapter using LiteLLM. One plugin (`web-fetch`) over MCP. Runs and spans stored. Minimal UI listing agents and runs with trace view. CLI: `varistha init`, `varistha apply -f agent.yaml`, `varistha run`. *Exit:* a YAML file becomes a running agent with a visible trace, end to end.

**Phase 2: Registry and lifecycle (weeks 4 to 5)** Versioned specs, stage transitions with gates, audit log, owners, kanban-style registry view by stage, diff between versions. *Exit:* an agent cannot reach Production without passing its gates, and every transition is audited.

**Phase 3: Approvals, guardrails and budgets (weeks 6 to 7)** Approval inbox with edit-and-approve, feedback capture (including edit diffs), policy engine with input, output and tool-call hooks, PII redaction, injection scan, rate limits, per-run and per-day budgets, global kill switch. *Exit:* an outbound action is impossible without approval at L1, and a runaway agent is stopped by its budget.

**Phase 4: Evals and confidence (weeks 8 to 9)** Eval suite format, dataset management, offline eval on version change, regression comparison between versions, sampled online evals, review-priority score from verifiable signals, eval results wired into promotion gates. *Exit:* promotion to Staging is blocked by a failing eval, and the UI shows version-over-version score changes.

**Phase 5: Plugin ecosystem and role packs (weeks 10 to 12)** Plugin manifest and toggle UI, plugins for web search, scrape (Crawl4AI and Playwright), email draft and send, X and LinkedIn through official APIs only, CRM export (CSV, HubSpot). Role packs: Lead Research and Competitor Intelligence with eval datasets. *Exit:* a new user installs a role pack, toggles plugins and gets a useful approved output within 15 minutes.

**Phase 6: Hardening and OTel fan-out (weeks 13 to 14)** OTel Collector profile with Langfuse or Grafana, auth and multi-user roles (admin, operator, viewer), secrets handling review, threat-model pass (prompt injection, SSRF in fetch plugins, credential leakage), load test, backup and restore docs. *Exit:* security checklist complete, 10 concurrent agents stable.

**Phase 7: Docs, packaging and launch (weeks 15 to 16)** See section 6.

## 6. Shipping plan

- **Repo hygiene:** Apache-2.0 LICENSE, CONTRIBUTING, CODE\_OF\_CONDUCT, SECURITY.md with a disclosure address, issue and PR templates, semantic versioning, CHANGELOG.
- **Distribution:** container images on GHCR, a `varistha` CLI on PyPI, one-line install script, Helm chart in a later release.
- **Docs site:** quickstart (5 minutes), concepts (spec, lifecycle, autonomy), role pack guides, plugin authoring guide, security and compliance notes, API reference. Fumadocs or Docusaurus.
- **Demo assets:** a 2-minute video of YAML to running agent to approval to promotion, and a public sandbox repo of example agents.
- **Launch:** Show HN, r/selfhosted, r/LocalLLaMA, X and LinkedIn posts from your own accounts, Product Hunt, relevant Discords. Lead with the lifecycle and approvals story, not a feature list.
- **Feedback loop:** pin a Discussions thread, tag good-first-issues, and publish a public roadmap.
- **Success metrics:** time-to-first-approved-output, stars as vanity only, weekly active self-hosted instances if you add opt-in telemetry, number of community plugins and role packs.
- **Sustainability:** keep the core permissive. If you want revenue later, consider hosted Varistha, enterprise SSO and audit exports, or a role pack marketplace.

## 7. Antigravity handoff

### 7.1 How to use this section

Antigravity is an agent-first IDE where agents plan, edit code, run the terminal and browser, and report back with artifacts. Verify the exact rules-file locations in your installed version, since they have changed between releases. Typically a project-level rules file (`AGENTS.md` or `GEMINI.md`) is read automatically, and reusable workflows live under `.agent/`.

Suggested flow:

1. Create the repo and put the `AGENTS.md` below in the root (also copy it to `GEMINI.md` if your version prefers that).
2. Save sections 1 to 5 of this doc as `docs/SPEC.md`.
3. Paste the kickoff prompt (7.3) into the Agent Manager, and require a written plan before any code.
4. Work one phase at a time. For each task use the template in 7.4.
5. Use separate agents in parallel only for independent areas (for example UI and docs), never for the same files.
6. Merge only when tests pass and the exit criteria for the task are checked off.

### 7.2 AGENTS.md (project rules)

```markdown
# Varistha: Agent Instructions

## Mission
Build Varistha, an open-source, self-hostable control plane to build, run, monitor and govern AI agents (AI employees) for startups. Read docs/SPEC.md before any task. It is the source of truth. If code and spec disagree, stop and ask.

## Non-negotiables
1. Work in small, verifiable increments. One task, one branch, one PR-sized change.
2. Plan first. For every task, write a short plan (files to touch, tests to add, risks) and wait for confirmation on anything larger than ~200 lines changed.
3. Tests are the acceptance gate. No feature is done without unit tests, and API or runtime features need an integration test. Run the full suite before declaring done.
4. Never add a dependency without stating its license, maintenance status and why. Only OSI-approved licenses in the core. AGPL or restricted-license tools may exist only as optional, separately installed plugins.
5. Default to the simplest stack in docs/SPEC.md section 4.1. Do not introduce Kafka, Redis, ClickHouse or Kubernetes into the default setup.
6. The default setup must work with `docker compose up` on a fresh clone with no manual steps beyond copying .env.example.

## Architecture rules
- Python 3.12, FastAPI, SQLAlchemy, Alembic, uv. UI: Next.js, TypeScript strict mode, shadcn/ui on Tailwind, pnpm. Follow docs/SPEC.md section 4.4 (UI and design system): semantic design tokens, no hard-coded colors, light and dark themes, empty/loading/error states on every screen.
- The agent runtime sits behind a Runtime interface. No LangGraph imports outside the adapter package.
- All capabilities are plugins exposed over MCP, described by a plugin manifest. No hardcoded tool logic in core.
- All models are accessed through LiteLLM. No provider SDK imports in core.
- Emit OpenTelemetry traces for every run, LLM call, tool call, guardrail check and approval wait. Use GenAI semantic conventions plus the varistha.* namespace.
- Database changes only through Alembic migrations. Specs are immutable once versioned.

## Security rules (treat as hard requirements)
- All content fetched from the web, email or users is untrusted data. Never let it modify system prompts, tool permissions or policies.
- Tool permissions, rate limits and approval requirements are enforced in code outside the model.
- Outbound actions (email, social posts, CRM writes) require approval at autonomy L1 and below. No code path may bypass this.
- Never log or trace secrets. Redact PII before export. Secrets are encrypted at rest.
- Fetch and scrape plugins must block private and loopback address ranges (SSRF protection).
- Do not implement scraping evasion, CAPTCHA bypass, fake accounts or terms-of-service circumvention. Use official APIs and user-supplied credentials.

## Code quality
- Type hints everywhere, mypy or pyright clean, ruff clean, ESLint clean.
- Small modules, clear names, docstrings on public interfaces.
- Errors are explicit and typed. No bare except. No silent fallbacks.
- Record notable decisions as ADRs in docs/adr/NNNN-title.md.

## Workflow per task
1. Restate the task and the relevant exit criteria from docs/SPEC.md.
2. Produce a plan artifact. Wait for approval if large.
3. Implement with tests.
4. Run lint, type-check, tests, and a compose smoke test.
5. Update docs and CHANGELOG.
6. Report: what changed, what was tested, known gaps, suggested next task.

## Out of scope until explicitly requested
Multi-tenant SaaS billing, marketplace, mobile apps, non-English UI, custom model training.

## When unsure
Ask one precise question rather than guessing. Prefer the boring, well-documented option.
```

### 7.3 Kickoff prompt (paste into Agent Manager)

```markdown
You are the lead engineer on Varistha. Read AGENTS.md and docs/SPEC.md fully.

Task: Phase 0, Foundations.

Do not write code yet. First produce a plan artifact that covers:
1. Proposed monorepo layout (apps/api, apps/worker, apps/ui, packages/cli, packages/spec, plugins/, docs/, deploy/).
2. Tooling choices for lint, type-check, test and CI, with license and maintenance status for each.
3. The docker-compose design (services, ports, volumes, healthchecks, env vars).
4. A task breakdown for Phase 0 and a draft breakdown for Phase 1, each task sized to a single PR.
5. The top five risks you see in the spec, and open questions for me.

Wait for my approval before implementing anything.
```

### 7.4 Per-task prompt template

```markdown
Task: <short name> (Phase <n>)
Context: <links to relevant SPEC sections and ADRs>
Goal: <one sentence of observable behaviour>
Acceptance criteria:
- <testable statement>
- <testable statement>
Constraints: follow AGENTS.md; touch only <paths>.
Process: plan first, then implement with tests, then run lint, type-check, tests and compose smoke test.
Deliver: summary, test evidence, doc updates, and the suggested next task.
```

### 7.5 Good first tasks for Phase 1, in order

1. Agent Spec JSON Schema, Pydantic models and a validator with good error messages, plus the example spec from section 3.4 as a fixture.
2. Database schema and migrations for agents, agent\_versions, runs and spans.
3. API endpoints to create, list and get agents and versions.
4. Runtime interface and the first LangGraph adapter running a single-prompt agent through LiteLLM.
5. MCP plugin host and the web-fetch plugin with SSRF protection.
6. OTel instrumentation, an OTLP receiver in the API and span persistence.
7. CLI commands init, apply and run.
8. Minimal UI: agents list, runs list and trace view.

## 8. Decisions you still need to make

1. **License:** Apache-2.0 (recommended for adoption) versus AGPL (protects against hosted forks, reduces adoption).
2. **Python versus TypeScript** for the core. Python is recommended for the ML and eval ecosystem, but TypeScript gives one language end to end.
3. **First vertical:** Lead Research is recommended because it exercises tools, approvals, evals and traces. Confirm.
4. **Default model path:** hosted API keys versus local models via Ollama for the quickstart. Supporting both through LiteLLM is recommended.
5. **Cloud story:** self-host only for now, or plan a hosted version later.

## Appendix A: Role catalog and scope boundaries

Every role carries a risk tag that becomes its default **autonomy ceiling** in the agent spec:

- **Green:** safe to automate, up to L2 or L3 once evals pass.
- **Amber:** the agent drafts or prepares and a human approves (L1).
- **Red:** advisory only (L0). The agent suggests, a human decides and acts.

### A.1 Tech and engineering (main scope)

- **Coding agent / PR author:** implements scoped tickets and opens PRs (Amber)
- **Code reviewer:** reviews PRs for bugs, style and security smells (Green)
- **QA / test writer:** generates and maintains tests, finds regressions (Green)
- **Bug triage agent:** dedupes, reproduces, labels and assigns issues (Green)
- **DevOps / CI watcher:** diagnoses failed builds, suggests fixes, proposes rollbacks (Amber)
- **Incident responder / on-call assistant:** summarizes alerts, drafts postmortems (Amber)
- **Infra cost optimizer:** flags waste across cloud bills (Green for reports, Amber for changes)
- **Security scanner:** dependency, secret and config audits (Green)
- **Documentation writer:** keeps docs, changelogs and API references in sync with code (Green)
- **Data engineer / analyst:** builds pipelines, answers data questions with SQL (Amber)
- **Release manager:** compiles release notes, checks gates (Amber)
- **Developer-relations assistant:** answers community questions, drafts tutorials (Amber)

### A.2 Product

- **User-feedback synthesizer:** clusters tickets, reviews and calls into themes (Green)
- **Competitor intelligence:** tracks launches, pricing, hiring and changelogs (Green)
- **Market and trend researcher:** industry reports, ICP research (Green)
- **PRD / spec drafter:** turns ideas and feedback into specs (Amber)
- **Roadmap and prioritization assistant:** scores backlog items against stated criteria (Red)
- **Product analytics agent:** funnels, retention and anomaly alerts (Green)
- **UX researcher helper:** drafts interview guides, summarizes sessions (Green)
- **Beta / waitlist manager:** onboarding comms, feedback collection (Amber)

### A.3 Marketing and publicity

- **Content writer:** blogs, newsletters, case studies (Amber)
- **Social media manager:** drafts and schedules posts on X, LinkedIn and others via official APIs (Amber)
- **SEO agent:** keyword research, content briefs, on-page audits (Green)
- **Content repurposer:** turns one asset into many formats (Green)
- **PR and media outreach:** finds journalists and podcasts, drafts pitches (Amber)
- **Community manager:** Discord and Slack moderation, FAQs, welcome flows (Amber)
- **Brand monitor / social listening:** mentions, sentiment, trend alerts (Green)
- **Ad copy and campaign analyst:** drafts creatives, reports performance (Amber)
- **Launch coordinator:** Product Hunt and Show HN checklists, assets, timelines (Amber)
- **Influencer and partnership scout:** identifies and ranks candidates (Green for research, Amber for outreach)
- **Visual / creative assistant:** briefs and prompt packs for design and image tools (Amber)

### A.4 Sales and client acquisition

- **Lead researcher / ICP finder:** builds and enriches lead lists (Green)
- **Lead qualifier / scorer:** applies your rubric to inbound leads (Green)
- **Outbound SDR drafter:** personalized sequences and follow-ups (Amber, always approval-gated)
- **Inbound responder:** replies to demo requests and website chat (Amber)
- **Meeting scheduler and prep:** briefs on the prospect before each call (Green)
- **CRM hygiene agent:** dedupes, updates fields, logs call notes (Green)
- **Proposal and quote drafter:** assembles proposals from templates (Amber)
- **Pipeline analyst:** forecasting and stalled-deal alerts (Green)
- **Account-expansion scout:** finds upsell signals in existing customers (Green)

### A.5 Customer success and support

- **Tier-1 support responder:** answers from docs and past tickets (Amber, can graduate to L2 for low-risk topics)
- **Ticket triage and routing:** classification, priority, escalation (Green)
- **Onboarding guide:** walks new customers through setup (Amber)
- **Churn-risk monitor:** usage-drop alerts, suggested outreach (Green)
- **Knowledge-base maintainer:** turns resolved tickets into articles (Green)
- **NPS / CSAT analyst:** survey summarization and trend reports (Green)
- **Renewal reminder agent:** drafts renewal notes (Amber)

### A.6 Operations and management

- **Chief-of-staff agent:** daily briefing, task chasing, meeting notes and action items (Green)
- **Project / program manager:** tracks milestones, flags blockers, writes status reports (Green)
- **Meeting assistant:** agendas, minutes, follow-ups (Green)
- **Internal helpdesk:** answers where-is-X and how-do-I-Y questions for staff (Green)
- **Vendor and tool manager:** tracks subscriptions, renewals and overlapping tools (Green)
- **Procurement researcher:** compares vendors, drafts RFQs (Amber)
- **OKR / KPI tracker:** pulls metrics into weekly scorecards (Green)
- **Process documenter:** turns workflows into SOPs (Green)
- **Travel and logistics coordinator:** itineraries and bookings prepared for approval (Amber)
- **Workflow-automation builder:** designs and tests new internal automations (Amber)

### A.7 HR, people and recruiting

- **Recruiting sourcer:** finds candidates matching a role (Amber, must respect platform terms and privacy law)
- **Job-description writer:** drafts postings and screening questions (Green)
- **Resume screener (assist only):** summarizes against stated criteria, never auto-rejects (Red or Amber, with bias auditing)
- **Interview scheduler and prep:** logistics, question banks, scorecards (Green)
- **Onboarding coordinator:** checklists, accounts, welcome materials (Amber)
- **Policy and handbook assistant:** answers employee questions from approved policy (Amber)
- **Engagement pulse analyst:** summarizes survey results (Green)
- **Learning and development curator:** training plans and resources (Green)

### A.8 Finance

- **Bookkeeping assistant:** categorizes transactions, flags anomalies (Amber)
- **Invoicing and AR follow-up:** drafts invoices and polite reminders (Amber)
- **Expense auditor:** policy-violation and duplicate detection (Green)
- **Budget vs actuals analyst:** variance reports (Green)
- **Cash-flow and runway forecaster:** scenarios from your data (Green, advisory)
- **Investor-update drafter:** monthly updates from metrics (Amber)
- **Fundraising research:** investor lists, fit scoring, data-room checklists (Green)
- **Financial-model assistant:** builds and sanity-checks spreadsheets (Amber)
- **Pricing analyst:** benchmarks and test suggestions (Red)

### A.9 Legal and compliance

- **Contract reviewer (first pass):** flags unusual clauses against your playbook (Amber, a lawyer decides)
- **NDA and template filler:** generates standard documents from templates (Amber)
- **Compliance tracker:** calendars filings, renewals and policy reviews (Green)
- **Privacy and data-request assistant:** logs and drafts responses to GDPR and DPDP requests (Amber)
- **Policy drafter:** first drafts of privacy policy, ToS and security policies (Amber, requires legal review)
- **Vendor risk assessor:** collects security questionnaires, summarizes risk (Green)
- **Regulatory watch:** monitors rule changes relevant to your sector (Green)
- **Audit-evidence collector:** gathers SOC 2 and ISO artifacts from your systems (Green)
- **IP watcher:** trademark and domain monitoring (Green)
- **Agent-governance auditor (Varistha-native):** reviews the platform's own audit logs, policy violations and approvals (Green)

### A.10 Executive and strategy

- **CEO / founder briefing agent:** one-page digest across metrics, news and risks (Green)
- **Board-pack preparer:** assembles slides and metrics for review (Amber)
- **Strategy research analyst:** market sizing, scenario memos (Green, advisory)
- **Red-team / devil's advocate:** challenges plans and assumptions (Green)
- **Decision-log keeper:** records decisions, rationale and follow-ups (Green)
- **M&A and partnership scanner:** identifies targets and synergies (Green, advisory)
- **Competitive war-room:** coordinates the competitor, product and sales agents into a weekly brief (Green)

### A.11 Platform and meta roles (Varistha-native)

- **Agent designer:** drafts new agent specs from a plain-language job description (Amber)
- **Eval author:** builds test datasets and judges for other agents (Amber)
- **Prompt and spec optimizer:** proposes improvements from failed runs and feedback (Amber)
- **Guardrail auditor:** tests agents against injection and policy bypass (Green)
- **Cost watchdog:** budget alerts and model-routing suggestions (Green)
- **Lifecycle steward:** nudges agents ready for promotion or retirement (Green, advisory)

### A.12 What will always remain out of scope

**Decisions and accountability that must stay human**

- Signing contracts, legal advice or legal sign-off
- Final hiring, firing, promotion and compensation decisions
- Fundraising negotiation, valuation and term sheets
- Company strategy ownership, ethical judgment and crisis calls
- Tax filing, audited financial statements and regulatory attestations

**Actions Varistha will not automate without a human in the loop**

- Moving money, paying invoices or changing payroll
- Production deploys with irreversible effects, deleting production data
- Sending outbound messages or posts at scale without approval gates and opt-out handling

**Things the project refuses by design**

- Fake accounts, astroturfing, impersonating real people or fabricated testimonials
- Scraping evasion, CAPTCHA bypass or terms-of-service circumvention
- Covert employee surveillance or automated discrimination in hiring
- Mass spam or purchased-list cold outreach

**Outside software entirely**

- Physical work, hardware, manufacturing and logistics
- Medical, safety-critical or life-critical decisions
- Building trust-heavy relationships such as investor, key-customer and cofounder dynamics

For compliance, finance and HR roles, the agent's value is preparation, monitoring and first drafts, while accountability stays with a named human owner.
