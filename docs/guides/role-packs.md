# Role Packs Guide

A **Role Pack** is a ready-to-run, production-tested AI employee package. Instead of configuring agents from scratch, startups can install role packs that come pre-bundled with curated system prompts, attached MCP tools, safety guardrails, budget limits, and baseline eval suites.

---

## 1. Built-in Role Packs Catalog

Varistha includes seven operational role packs located in `role-packs/`:

### 1. Lead Research (`role-packs/lead-research`)
- **Role**: Discovers prospective B2B accounts matching an ICP, extracts verified executive contacts, technographic signals, and drafts personalized introductory notes.
- **Autonomy**: `L1` (Requires human approval before saving leads or drafting outreach).
- **Default Plugins**: `web-search`, `web-scrape`, `email-draft`.
- **Budgets**: $0.50 / run, $10.00 / day.

### 2. Competitor Intelligence (`role-packs/competitor-intel`)
- **Role**: Monitors competitor web domains, blogs, changelogs, and pricing pages for strategic updates and positioning shifts.
- **Autonomy**: `L2` (Supervised data extraction with CRM logging).
- **Default Plugins**: `web-search`, `web-scrape`, `crm-export`.
- **Schedule**: Daily at 06:00 UTC.

### 3. Outbound SDR (`role-packs/outbound-sdr`)
- **Role**: Conducts personalized outbound prospect engagement subject to human review. Generates high-conversion email drafts tailored to prospect pain points.
- **Autonomy**: `L1` (Mandatory human approval gate on all drafted emails).
- **Default Plugins**: `web-fetch`, `email-draft`, `email-send`.

### 4. Support Responder (`role-packs/support-responder`)
- **Role**: Triages incoming customer support inquiries, searches documentation bases, and prepares drafted responses for human agent sign-off.
- **Autonomy**: `L1` (Human approval required before replying to tickets).
- **Default Plugins**: `web-fetch`, `email-draft`.

### 5. Content Repurposer (`role-packs/content-repurposer`)
- **Role**: Reads published blog posts or release notes and creates punchy, platform-optimized threads for X and LinkedIn.
- **Autonomy**: `L2` (Drafts created automatically; posting gated by policy).
- **Default Plugins**: `web-fetch`, `linkedin-post`, `x-post`.

### 6. Lead Qualifier (`role-packs/lead-qualifier`)
- **Role**: Evaluates inbound signups against revenue and ICP criteria, flagging high-priority leads for immediate sales follow-up.
- **Autonomy**: `L2`.
- **Default Plugins**: `web-fetch`, `crm-export`.

### 7. Chief of Staff (`role-packs/chief-of-staff`)
- **Role**: Synthesizes cross-functional metrics, pending approval queues, and project milestones into daily executive briefs.
- **Autonomy**: `L2`.
- **Default Plugins**: `web-fetch`, `crm-export`.

---

## 2. Installing a Role Pack

You can install any role pack directly using the Varistha CLI:

```bash
# Apply the Lead Research role pack
varistha apply -f role-packs/lead-research/agent.yaml

# Run an initial evaluation suite to verify baseline performance
varistha eval run role-packs/lead-research/evals/lead-research.yaml
```

Once applied, the agent appears in your **Registry** at the `prototype` stage.

---

## 3. Role Pack Anatomy

A canonical role pack directory contains:

```
role-packs/lead-research/
├── agent.yaml           # Declarative Agent Spec
├── README.md            # Usage and configuration instructions
├── prompts/
│   └── instructions.md  # Detailed system instructions and few-shot examples
└── evals/
    ├── dataset.json     # Test cases with input variables and expected outputs
    └── suite.yaml       # Eval suite configuration with pass rate thresholds
```

---

## 4. Creating a Custom Role Pack

To package your own AI employee:
1. Create a directory under `role-packs/<my-role>/`.
2. Write `agent.yaml` following the standard Agent Spec schema (`apiVersion: varistha/v1`).
3. Define prompts in `prompts/instructions.md`.
4. Include an evaluation dataset with at least 5 representative test cases in `evals/`.
5. Verify the pack:
   ```bash
   varistha apply -f role-packs/<my-role>/agent.yaml
   varistha eval run role-packs/<my-role>/evals/suite.yaml
   ```
