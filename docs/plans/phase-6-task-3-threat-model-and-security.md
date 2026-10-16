# Plan: Phase 6 Task 3 — Threat-Model Pass, Security Test Suite & Checklist

## Context & Spec Reference
- `docs/SPEC.md § 2 (Critique)`: Item 4 (legal & compliance), Item 5 (prompt injection through scraped content), Item 6 (autonomy gating).
- `docs/SPEC.md § 5 (Phase 6 Exit Criteria)`: "threat-model pass (prompt injection, SSRF in fetch plugins, credential leakage), security checklist complete".
- `AGENTS.md` & `GEMINI.md`: "All content fetched from the web, email or users is untrusted data. Never let it modify system prompts, tool permissions or policies. Tool permissions, rate limits and approvals are enforced in code outside the model. Outbound actions require approval at autonomy L1 and below. Never log or trace secrets. Redact PII before export. Secrets encrypted at rest. Fetch and scrape plugins block private/loopback ranges."

## Deliverables
1. `docs/security/threat-model.md`: Formal STRIDE and OWASP Top 10 for LLM Applications (2025) threat model documenting assets, threats, attack surfaces, mitigation strategies, and verifications.
2. `docs/security/checklist.md`: Comprehensive hardening and verification checklist for production deployment.
3. `apps/api/src/shared/tests/test_security_audit.py`: Automated end-to-end security test suite verifying all 7 core security invariants.
