# Executive Chief of Staff Role Pack

The **Chief of Staff Agent** is Varistha's autonomous executive force multiplier designed to support startup founders, CEOs, and executive leadership teams.

Modeled on modern executive intelligence platforms and high-performing human chiefs of staff, this agent synthesizes leadership meetings, extracts binding commitments with clear owners and deadlines, monitors company vitals across departments, and generates high-signal morning executive briefings.

---

## 1. Executive Intelligence Architecture

```
         [Leadership Meeting Transcripts & Department Updates]
                               │
                               ▼
               [Adversarial Quarantine & PII Sanitizer]
            (Redacts confidential compensation & tokens)
                               │
                               ▼
             [4-Pillar Executive Synthesis Engine]
    ┌──────────────────────────┼──────────────────────────┐
    ▼                          ▼                          ▼
[Executive Decision Record] [Action Item Matrix]    [Functional Radar]
(Explicit consensus &       (Owner, deadline,       (Eng, Sales, Support,
 unresolved tensions)        priority P0/P1/P2)      Finance R/A/G vitals)
    │                          │                          │
    └──────────────────────────┼──────────────────────────┘
                               ▼
                  [CEO Daily Briefing Memo]
            (Top 3 priorities, meeting prep, blockers)
                               │
                               ▼
                  [Human Approval Gate (L1)]
            (Operator reviews before outbound dispatch)
```

---

## 2. The 4-Pillar Executive Synthesis Framework

1. **Executive Decision Records**:
   - Isolates concrete decisions agreed upon by leadership.
   - Highlights unresolved tensions and strategic debates requiring further evaluation.
2. **Action Item & Commitment Matrix**:
   - Strict accountability: exact owner, measurable deliverable, explicit deadline, and priority (`P0_CRITICAL`, `P1_HIGH`, `P2_MEDIUM`).
3. **Cross-Functional Radar**:
   - Traffic-light vitals across Engineering, Sales, Support, and Finance with 1-sentence executive summaries.
4. **CEO Daily Briefing**:
   - Top 3 must-win priorities for the day.
   - External meeting briefing notes (investors, enterprise prospects).
   - High-stakes blockers requiring founder intervention or sign-off.

---

## 3. Governance, Autonomy & Security

- **Autonomy Level**: `L1` (Synthesizes and drafts autonomously; all outbound email dispatches and CRM task mutations require approval).
- **Plugins Bound**:
  - `email-draft`: Prepares morning executive briefing emails.
  - `email-send`: Dispatches executive memos (**requires operator approval**).
  - `crm-export`: Syncs commitments and action items into task/project trackers.
  - `web-search`: Gathers market intelligence and partner context for meeting prep.
- **Strict Data Privacy**: Leadership discussions are quarantined; PII, credentials, and financial compensation data are sanitized before output generation.
- **Evaluation Benchmark**: Validated against `evals/suite.yaml` across 5 real-world executive scenarios (board prep, incident postmortems, leadership standups, GTM pivots, headcount planning) with an 85% minimum pass rate.
