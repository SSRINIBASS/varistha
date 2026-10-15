# Master Plan: Phase 5 — Plugin Ecosystem & Role Packs

## Context & Objectives
In accordance with `docs/SPEC.md § 5` and user instructions:
- **Phase 5 Goal**: Build the complete plugin ecosystem (manifests, toggle UI, safe MCP execution) and top-tier Role Packs with evaluation datasets and prompts.
- **Exit Criteria**: A new user installs a role pack, toggles plugins, and gets a useful approved output within 15 minutes.
- **Agent Shipping Mandate**: For every individual agent in the role packs:
  1. Conduct deep niche research on existing state-of-the-art implementations.
  2. Synthesize best-in-class prompt engineering, few-shot rubrics, output schemas, and guardrails.
  3. Ship each agent in its own isolated commit with dedicated unit tests, eval suites, and test cases.

---

## Phase 5 Task Sequence

### Task 1: Plugin Manifest Registry & UI Toggle System
- **Scope**:
  - Backend: REST endpoints `GET /api/v1/plugins`, `GET /api/v1/plugins/{name}`, and plugin status verification in `PluginHost`.
  - Frontend: Plugin Explorer & Toggle UI at `/plugins` and within Agent Detail/Edit view.
  - Manifest validation and permissions enforcement outside the model.
- **Acceptance Gate**:
  - Unit tests for plugin API and UI toggles.
  - Typecheck, lint, pytest, and Vitest passing.

### Task 2: Core Research & Data Plugins
- **Scope**:
  - `web-search`: Pluggable search (DuckDuckGo / Tavily / SearXNG) returning structured citations and titles with rate limiting.
  - `web-scrape`: Deep article and page extractor using Crawl4AI / Playwright with SSRF filters.
  - `crm-export`: CSV exporter and HubSpot CRM payload generator with schema validation.
- **Acceptance Gate**:
  - Unit tests for all 3 plugins with mocked network and SSRF checks.

### Task 3: Outbound & Communication Plugins (Strictly Gated)
- **Scope**:
  - `email-draft`: Contextual email composer with personalization tokens.
  - `email-send`: Outbound SMTP/API sender strictly flagged `requires_approval: true`, blocking execution without approval at L0/L1.
  - `x-post`: Official X (Twitter) v2 API poster flagged `requires_approval: true` with strict character and rate checks.
  - `linkedin-post`: Official LinkedIn v2 API poster flagged `requires_approval: true` with format checks.
- **Acceptance Gate**:
  - Tests ensuring no bypass of human approval at autonomy L0/L1.

### Task 4 onwards: Individual Role Pack Agents (1 Commit Per Agent)
Each agent is researched thoroughly, crafted to supersede all existing open-source counterparts, and shipped with complete eval suites in its own commit:
1. **Agent 1: Lead Researcher & ICP Finder** (`sales/lead-researcher`)
   - Research: Lindy, Clay, Apollo, Relevance AI lead research agents.
   - Deliverable: Spec, prompt, tools, eval dataset, isolated commit.
2. **Agent 2: Inbound Lead Qualifier & Scorer** (`sales/lead-qualifier`)
   - Research: Drift, Qualified, HubSpot AI qualifiers.
   - Deliverable: Spec, rubric, schema validation, eval dataset, isolated commit.
3. **Agent 3: Outbound Personalized SDR Drafter** (`sales/outbound-sdr`)
   - Research: Regie.ai, Lavender, Instantly AI copywriters.
   - Deliverable: Spec, cold outreach templates, objection handling, approval gates, isolated commit.
4. **Agent 4: Competitor Intelligence & Diff Watcher** (`market-intel/competitor-watcher`)
   - Research: Klue, Crayon, Visualping intelligence feeds.
   - Deliverable: Spec, website comparison, positioning matrix, eval dataset, isolated commit.
5. **Agent 5: Content Repurposer & Multi-Channel Drafter** (`marketing/content-repurposer`)
   - Research: Castmagic, Taplio, Jasper campaign repurposers.
   - Deliverable: Spec, blog-to-social prompts, formatting guardrails, eval dataset, isolated commit.
6. **Agent 6: Tier-1 Customer Support & Triage Agent** (`support/support-responder`)
   - Research: Intercom Fin, Decagon, Zendesk AI agents.
   - Deliverable: Spec, grounding checks, escalation criteria, eval dataset, isolated commit.
7. **Agent 7: Meeting Scribe & Chief-of-Staff Briefing Agent** (`operations/chief-of-staff`)
   - Research: Otter, Fireflies, Supernormal executive assistants.
   - Deliverable: Spec, action item extractor, risk flagger, eval dataset, isolated commit.

---

## Phase 5 Exit Gate Checklist
- [ ] All plugins implemented with manifest schemas, test coverage, and SSRF protection.
- [ ] Plugin toggle UI and Agent spec bindings functional.
- [ ] All role pack agents implemented with prompt files, eval suites, and test assertions.
- [ ] Automated CI and Code Review workflows 100% green on master and main.
- [ ] Checkpoint document `docs/checkpoints/phase-5-complete.md` and git tag `phase-5-complete`.
