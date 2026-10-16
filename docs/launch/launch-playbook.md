# Varistha Launch Playbook

This playbook outlines the public launch narrative, channel-specific copies, asset positioning, and community onboarding workflow for Varistha v0.1.0.

---

## 1. Positioning & Narrative

### The Core Story
> **"Most AI agents deployed today operate like scripts running in the dark. Varistha is the open-source control plane that brings operational discipline, stage gates, human approvals, and token budget limits to AI employees."**

### Key Narrative Pillars
- **Lead with Lifecycle & Approvals, not Feature Hype**: Emphasize that building prompts is easy; operating agents safely with audit trails, stage promotion gates (Draft &rarr; Prototype &rarr; Staging &rarr; Production), and mandatory human sign-off on outbound writes is the hard part.
- **Enforcement Outside the Model**: Safety policies, PII redactions, SSRF network filters, and budget limits are enforced in deterministic application code, never entrusted to the LLM itself.
- **Zero Vendor Lock-in & Self-Hostable**: 4 containers in `docker compose up` with zero mandatory cloud accounts. Works with OpenAI, Anthropic, or 100% locally with Ollama and vLLM.

---

## 2. Hacker News: Show HN

**Title**:
```
Show HN: Varistha – Open-source control plane to run, monitor and govern AI agents
```

**First Comment (Story & Architecture)**:
```markdown
Hey HN,

We're building Varistha (https://github.com/SSRINIBASS/varistha), an open-source, self-hostable control plane to run, monitor, and govern autonomous AI agents (AI employees) for startups.

Like many teams, we experimented with LangChain, CrewAI, and custom scripts for tasks like B2B lead enrichment, competitor tracking, and customer triage. They worked in prototypes, but running them in production was terrifying:
1. No central registry of who owned which agent or what version was running.
2. An agent could hallucinate and fire off live outbound emails or API calls with zero human oversight.
3. A single loop bug or recursive tool invocation could burn through hundreds of dollars in API credits overnight.
4. Telemetry was fragmented across log aggregators with zero GenAI token or cost visibility.

We built Varistha to solve this. It provides three core pillars:
- **Build**: Declarative YAML agent specifications with semver versioning, fallback models, MCP plugins, and ready-to-run role packs.
- **Run**: Durable execution engine (LangGraph behind a strict Runtime adapter) with schedule, webhook, and manual triggers.
- **Govern (AgentOps)**: Stage promotion gates (Draft -> Prototype -> Staging -> Production), side-by-side human-in-the-loop approval inbox for outbound writes, automated guardrails (PII redaction, prompt injection scans), and hard per-run/per-day budget limits with a global emergency kill switch.

### Architecture Highlights
- Backend: Python 3.12, FastAPI, SQLAlchemy, PostgreSQL 16 + pgvector.
- Model Gateway: LiteLLM for multi-provider routing (OpenAI, Claude, Ollama, vLLM) with zero provider SDKs in core.
- Extensibility: All capabilities are sandboxed Model Context Protocol (MCP) plugins.
- Observability: OpenTelemetry GenAI spans fanning out to Langfuse, Grafana Tempo, or built-in Postgres storage.
- Frontend: Next.js 14, shadcn/ui, Tailwind CSS.

### Try it in 2 minutes:
git clone https://github.com/SSRINIBASS/varistha.git
cd varistha
cp deploy/.env.example deploy/.env
docker compose -f deploy/docker-compose.yml up -d
# Dashboard: http://localhost:3000

We would love your feedback on our agent spec schema and how you govern autonomous workflows in your teams!
```

---

## 3. Reddit Launch Posts

### Subreddit: r/selfhosted
**Title**:
```
Varistha: Self-hosted open-source control plane for AI agents (Docker Compose, no SaaS required)
```

**Body**:
```markdown
Hi r/selfhosted,

We just released Varistha v0.1.0 (https://github.com/SSRINIBASS/varistha) – an open-source control plane for running and monitoring autonomous AI agents on your own hardware.

Key self-hosting highlights:
- 100% self-contained: `docker compose -f deploy/docker-compose.yml up -d` brings up everything (Postgres+pgvector, API, worker, and Next.js UI).
- Zero cloud tracking or mandatory telemetry.
- Connects directly to local Ollama or vLLM instances via LiteLLM without needing external API keys.
- AES-256-GCM encrypted secrets vault at rest.
- Hard spending limits and kill switches so a runaway agent cannot exhaust resources.

Full quickstart and docs: https://github.com/SSRINIBASS/varistha/blob/main/docs/guides/quickstart.md
Feedback and PRs welcome!
```

### Subreddit: r/LocalLLaMA
**Title**:
```
Varistha v0.1.0: Self-hosted control plane for local AI agents with Ollama / vLLM support
```

**Body**:
```markdown
Hey everyone,

If you are running local models with Ollama or vLLM for business automation, we built Varistha (https://github.com/SSRINIBASS/varistha) to give you an enterprise-grade control plane:
- Route to `ollama/llama3.3` or `vllm/*` as primary models with automatic cloud fallback if needed.
- Sandboxed MCP tools with SSRF denylists blocking access to local subnet IPs.
- Human-in-the-loop review inbox with side-by-side edit diffs before any tool writes outbound data.
- OpenTelemetry GenAI tracing to visualize exact token latency and tool calls.
- Apache-2.0 licensed throughout.

Check out the repo and let us know what local agent workflows you'd like to see!
```

---

## 4. Product Hunt Launch Kit

- **Name**: Varistha
- **Tagline**: Open-source control plane to run, monitor & govern AI agents
- **Categories**: Developer Tools, Open Source, Artificial Intelligence, Productivity
- **Maker Comment**:
  > "Hi Product Hunt! We created Varistha because startups don't just need AI agents that can write text; they need operational discipline. Varistha provides stage gates, human-in-the-loop approvals, PII guardrails, token budget limits, and OpenTelemetry observability. It's 100% open-source under Apache-2.0 and self-hostable with one Docker Compose command. Check it out and let us know what you think!"

---

## 5. Social Media Launch Threads (X / Twitter & LinkedIn)

**Tweet 1 (Hook)**:
> Autonomous AI agents in startups are currently operating like untracked scripts in the dark.
>
> Today, we're launching Varistha: an open-source, self-hostable control plane to build, run, monitor, and govern AI employees. 🧵👇

**Tweet 2 (The Problem)**:
> Prompting an LLM is easy. But what happens when an agent:
> - Hallucinates and emails a real customer?
> - Hits an infinite loop and burns $500 in tokens?
> - Leaks internal PII in outbound API requests?
> You need governance *outside* the model.

**Tweet 3 (The Solution)**:
> Varistha provides three pillars:
> 1. Build: Declarative YAML specs, role packs, and MCP plugins.
> 2. Run: Checkpointed LangGraph runtime with multi-trigger dispatch.
> 3. Govern: Human-in-the-loop approval inbox with side-by-side diffs, guardrails, and hard budget caps.

**Tweet 4 (Architecture)**:
> Built on Python 3.12, FastAPI, Next.js, shadcn/ui, PostgreSQL with pgvector, and OpenTelemetry GenAI fan-out.
> 
> Works with any model via LiteLLM or 100% locally with Ollama.
> 
> Apache-2.0. Self-hostable with `docker compose up`.

**Tweet 5 (CTA)**:
> Star the repo on GitHub: https://github.com/SSRINIBASS/varistha
> 
> Read the 5-minute quickstart: https://github.com/SSRINIBASS/varistha/blob/main/docs/guides/quickstart.md
> 
> What AI employees are you building? Let us know below!

---

## 6. Community Feedback & Triage Protocol

1. **GitHub Discussions**:
   - Pin "Welcome to Varistha! Share your feedback & use cases here".
   - Create category `Show and Tell` for community-built role packs and plugins.
2. **Good First Issues**:
   - Tag beginner-friendly tasks with `good-first-issue` (e.g., adding a Slack notification plugin, new eval metrics).
3. **Issue Triage**:
   - Acknowledge all bug reports within 24 hours.
   - Security issues handled according to [SECURITY.md](../../SECURITY.md).
