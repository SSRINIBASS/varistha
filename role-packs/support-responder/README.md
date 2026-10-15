# Tier-1 Support Responder & Technical Triage Role Pack

The **Support Responder Agent** is Varistha's autonomous customer operations specialist designed for rapid inbound ticket classification, sentiment and urgency scoring, documentation-grounded technical troubleshooting, and automated escalation.

Modeled on modern customer service AI platforms like **Intercom Fin**, **Decagon**, and **Zendesk AI**, this agent combines deep technical accuracy with empathetic customer communication while strictly preventing hallucinations and unauthorized promises.

---

## 1. Support & Triage Lifecycle Architecture

```
                  [Inbound Customer Ticket]
          (Error logs / Inquiries / Billing / Outages)
                             │
                             ▼
              [Adversarial Quarantine & Clean]
           (Filters prompt injection in user input)
                             │
                             ▼
         [Intent Classification & Sentiment Scoring]
    ┌────────────────────────┼────────────────────────┐
    ▼                        ▼                        ▼
[Category Mapping]      [Urgency & SLA]          [Sentiment]
(Auth, Billing, Bug,    (CRITICAL_SLA, HIGH,     (FRUSTRATED,
 Rate Limit, How-To)     NORMAL, LOW)             NEUTRAL, POSITIVE)
    │                        │                        │
    └────────────────────────┼────────────────────────┘
                             ▼
                 [Escalation Decision Matrix]
           ┌─────────────────┴─────────────────┐
           ▼                                   ▼
 [Standard / How-To Issue]            [Critical / Billing / Bug]
 (Generates step-by-step fix)         (Flags escalation target:
                                       on-call or billing-ops)
           │                                   │
           └─────────────────┬─────────────────┘
                             ▼
                 [Human Approval Gate (L1)]
           (Operator reviews before outbound email send)
```

---

## 2. Intent Taxonomy & SLA Matrix

1. **Classification Categories**:
   - `AUTHENTICATION_ERROR`: API tokens, JWT expiration, OAuth, SSO.
   - `RATE_LIMIT_QUOTA`: 429 errors, budget circuit breaker triggers, rate throttles.
   - `BUG_REPORT`: Runtime exceptions, connection pool exhaustion, crashes.
   - `BILLING_DISPUTE`: Overage charges, payment failures, refund requests.
   - `HOW_TO_DOCS`: Configuration, Docker Compose setup, CLI usage.
   - `FEATURE_REQUEST`: Provider integrations, new plugin requests.

2. **Urgency & Response Targets**:
   - `CRITICAL_SLA`: Fleet/cluster outages, production data risk (< 15 min SLA). Escalates to `on-call-engineering`.
   - `HIGH`: Workflow blocking errors, billing locks (< 1 hr SLA).
   - `NORMAL`: Configuration issues, minor non-blocking errors (< 4 hr SLA).
   - `LOW`: Feature requests, documentation typos (< 24 hr SLA).

3. **Grounding & Empathy Rules**:
   - Direct, numbered resolution steps with code/CLI snippets.
   - No fabricated workarounds or false promises.
   - Empathetic validation of customer frustration without defensive excuses.

---

## 3. Governance, Autonomy & Safety

- **Autonomy Level**: `L1` (Drafts responses and tags tickets autonomously; email dispatches require human approval).
- **Plugins Bound**:
  - `email-draft`: Prepares contextual email replies.
  - `email-send`: Dispatches resolution emails (**requires operator approval**).
  - `crm-export`: Updates ticket records, tags, and escalation metadata.
  - `web-search`: Searches official docs and status pages.
- **Untrusted Input Protection**: Ticket text is quarantined to ensure malicious instructions or SQL/prompt injections cannot tamper with system logic.
- **Evaluation Benchmark**: Validated against `evals/suite.yaml` across 5 real-world scenarios (DB timeouts, 401s, billing disputes, budget caps, feature requests) with an 85% minimum pass rate.
