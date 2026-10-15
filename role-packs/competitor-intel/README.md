# Competitor Intelligence & Diff Watcher Role Pack

The **Competitor Intelligence & Diff Watcher Agent** is Varistha's autonomous competitive intelligence analyst built for monitoring rival websites, pricing structures, changelogs, and positioning claims.

Modeled on modern competitive intelligence platforms like **Klue**, **Crayon**, and **Visualping**, this agent filters out cosmetic website updates to isolate strategic market moves and synthesizes immediate, actionable sales battlecards and executive briefings.

---

## 1. Intelligence Architecture & Differential Analysis

```
[Competitor Public Sources (Websites / Pricing / Changelogs)]
                           │
                           ▼
              [Adversarial Quarantine]
   (Isolates prompt injection & untrusted DOM content)
                           │
                           ▼
          [Semantic Differential Analysis]
   ┌───────────────────────┼───────────────────────┐
   ▼                       ▼                       ▼
PRICING_CHANGE     FEATURE_RELEASE         POSITIONING_PIVOT
(Quotas/Tiers)     (SDKs/Engines)          (Headline Pivots)
                           │
                           ▼
               [Threat Severity Rating]
              (CRITICAL / HIGH / MED / LOW)
                           │
                           ▼
           [Sales Battlecard & Action Plan]
   (Where We Win, Trap Questions, Quick Rebuttals)
```

---

## 2. Intelligence Vectors & Threat Ratings

1. **Intelligence Vectors**:
   - `PRICING_CHANGE`: Shifts in tiers, usage metering, seat pricing, or free tier deprecation.
   - `FEATURE_RELEASE`: New adapters, SDKs, agent frameworks, or governance features.
   - `POSITIONING_PIVOT`: Core marketing shifts (e.g. RPA to Autonomous AI Employees).
   - `PARTNERSHIP_INTEGRATION`: Cloud marketplace listings, model provider alliances.
   - `NOISE_IGNORE`: Copyright date bumps, cosmetic CSS padding, layout redesigns.

2. **Automated Battlecard Output**:
   - **Where We Win**: Moats such as VPC self-hosting, deterministic guardrails outside the model, and OpenTelemetry standards.
   - **Where They Win**: Honest analysis of their advantages (e.g. hosted billing, turnkey UI).
   - **Trap-Setting Questions**: High-impact discovery questions sales reps give to prospects.
   - **Quick Rebuttal**: Concise response for live objections.

---

## 3. Governance, Autonomy & Security

- **Autonomy Level**: `L1` (Autonomous analysis; notifications and downstream updates flagged).
- **Plugins Bound**:
  - `web-search`: Discover latest releases, announcements, and news.
  - `web-scrape`: Scrape and diff public pages with SSRF protection.
- **Untrusted Content Quarantine**: Competitor pages are treated as hostile external input; hidden prompt injection instructions are ignored.
- **Evaluation Benchmark**: Validated against `evals/suite.yaml` across 5 real-world competitive shift scenarios with a minimum pass rate of 85%.
