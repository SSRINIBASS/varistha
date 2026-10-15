# Lead Researcher & ICP Qualification Role Pack

The **Lead Researcher & ICP Qualification Agent** is Varistha's production-ready AI employee for outbound account intelligence, ICP scoring, and executive stakeholder mapping.

Modeled on modern sales intelligence tools like **Claygent**, **Lindy**, and **Apollo Copilot**, this agent runs a multi-source research pipeline to discover target companies, score them against strict B2B criteria, and stage clean records for CRM export without hallucinating credentials or performing unverified outbound actions.

---

## 1. Capabilities & Workflow

```
[Target Account Inquiry]
        │
        ▼
[web-search Plugin]  ──> Queries company domain, funding news, leadership appointments
        │
        ▼
[web-scrape Plugin]  ──> Fetches homepage, About Us, Careers, and Pricing (SSRF safe)
        │
        ▼
[ICP Scoring Matrix] ──> Evaluates 4 dimensions (0-100 pts) -> Assigns ICP Tier
        │
        ▼
[Decision-Maker Map] ──> Identifies 2-3 executive personas + tailored pain points
        │
        ▼
[crm-export Plugin]  ──> Formats validated lead object into CSV, HubSpot, or Salesforce format
```

---

## 2. ICP Scoring Matrix

The agent scores each account across four 25-point dimensions (100 points total):

1. **Industry & Business Model (0-25 pts)**:
   - 25: B2B SaaS, Developer Tooling, AI Infrastructure.
   - 15: Fintech, Enterprise Software, HealthTech B2B.
   - 5: Traditional IT, Agency, Consulting.
   - 0: Consumer D2C, Local Services, Brick-and-Mortar.
2. **Company Size & Traction (0-25 pts)**:
   - 25: 50-250 employees (Sweet spot).
   - 20: 20-50 or 250-500 employees.
   - 10: 10-20 or 500-1000 employees.
   - 0: Solopreneur or 10,000+ massive enterprise.
3. **AI & Technology Adoption (0-25 pts)**:
   - 25: Deploying LLMs, autonomous agents, or AI features.
   - 15: Modern cloud-native microservices architecture.
   - 5: Legacy on-premises software undergoing migration.
   - 0: Non-technical operations.
4. **Buying Signals & Timing (0-25 pts)**:
   - 25: 2+ high-conviction signals (recent funding round, AI hiring sprint, leadership change).
   - 15: 1 active buying signal in the last 90 days.
   - 5: Normal ongoing operations.
   - 0: Downsizing, layoffs, or hiring freeze.

### Tiers:
- **`TIER_1_PRIORITY`** (80-100): High priority. Routed immediately to Outbound SDR.
- **`TIER_2_QUALIFIED`** (60-79): Qualified account. Placed in standard outreach sequence.
- **`TIER_3_NURTURE`** (40-59): Long-term potential. Added to marketing newsletter.
- **`DISQUALIFIED`** (< 40): Outside target market. Stored in CRM as disqualified.

---

## 3. Governance, Autonomy & Safety

- **Autonomy Level**: `L1` (Human-in-the-Loop for Outbound). The agent performs web searches, content extraction, and scoring autonomously, but pauses for human approval before sending any email or making live CRM modifications.
- **Untrusted Content Quarantine**: All content fetched via `web-search` and `web-scrape` is flagged `untrusted: true`. The runtime enforces injection scanning and PII masking.
- **Deterministic Evaluation**: Includes `evals/suite.yaml` verifying classification across AI startups, fintech platforms, devtools, and disqualified consumer brands.
