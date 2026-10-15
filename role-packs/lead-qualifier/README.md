# Inbound Lead Qualifier & Scorer Role Pack

The **Inbound Lead Qualifier & Scorer Agent** is Varistha's autonomous AI employee designed to qualify inbound contact requests, demo submissions, and customer inquiries against a multi-pillar **BANT / MEDDPICC scoring matrix**.

Modeled on enterprise qualification platforms like **Drift**, **Qualified**, and **HubSpot AI Assistant**, this agent eliminates manual SDR triage fatigue, scores inbound leads in real time, extracts intent, and intelligently routes opportunities to Account Executives, discovery cadences, or self-serve developer paths.

---

## 1. Capabilities & Architecture

```
[Inbound Form / Demo Request]
              │
              ▼
    [Input Guardrails]         ──> PII Masking & Injection Scanning
              │
              ▼
   [BANT / MEDDPICC Matrix]    ──> Evaluates 4 Pillars (0-100 pts)
              │
              ▼
  [Intent & Routing Engine]    ──> Classifies Intent & Destination
              │
              ▼
    [Enrichment & Gaps]        ──> Detects missing data & generates follow-up questions
              │
              ▼
      [CRM & Draft Hub]        ──> crm-export stages lead & email-draft drafts response
```

---

## 2. Qualification Scoring Matrix (0-100 pts)

1. **Need & Use Case Alignment (0-30 pts)**:
   - 30 pts: Critical problem matching Varistha (agent governance, OTel tracing, deterministic guardrails, spend limits).
   - 20 pts: General AI/LLM operational interest.
   - 10 pts: Exploratory AI curiosity.
   - 0 pts: Unrelated inquiry.
2. **Authority / Stakeholder Role (0-25 pts)**:
   - 25 pts: Economic Buyer / C-Level (Founder, CEO, CTO, VP Engineering, Head of AI).
   - 18 pts: Technical Champion (Staff Engineer, AI Architect, Product Manager).
   - 10 pts: Individual Contributor.
   - 0 pts: Student, applicant, non-commercial user.
3. **Company Stage & Business Domain (0-25 pts)**:
   - 25 pts: Verified corporate domain from funded startup or enterprise (20+ headcount).
   - 15 pts: Corporate domain from early-stage startup (< 20 headcount).
   - 5 pts: Freemail domain (@gmail.com) with valid corporate context.
   - 0 pts: Anonymous or freemail with no business context (automatic 15 pt penalty).
4. **Timeline & Commercial Urgency (0-20 pts)**:
   - 20 pts: Active pilot / evaluating rollout this month.
   - 12 pts: Medium-term initiative (3-6 months).
   - 5 pts: Long-term exploration.
   - 0 pts: No commercial timeline.

### Routing Tiers:
- **`AE_PRIORITY_DEMO`** (80-100): High conviction. Direct booking on AE calendar.
- **`SDR_DISCOVERY_CALL`** (60-79): Qualified prospect. Enters SDR discovery sequence.
- **`SELF_SERVE_PRODUCT`** (40-59): Indie developer or early team. Routed to open-source docs.
- **`COMMUNITY_TIER`** (20-39): Educational / hobbyist. Routed to Discord community.
- **`DISQUALIFIED`** (< 20): Solicitations, spam, academic research.

---

## 3. Governance, Autonomy & Safety

- **Autonomy Level**: `L1` (Human in the Loop for Outbound).
- **Plugins Bound**: `crm-export`, `email-draft`.
- **Guardrails**:
  - `input`: `pii-redact`, `injection-scan` (protects customer privacy and blocks adversarial prompt injections).
  - `output`: `schema-valid` (guarantees valid structured JSON qualification payload).
  - `tools`: `outbound-needs-approval` (human must approve sending any drafted email).
- **Evaluation Suite**: Validated against `evals/suite.yaml` across enterprise buyers, tech leads, indie hackers, students, and spam.
