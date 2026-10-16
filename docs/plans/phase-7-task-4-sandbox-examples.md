# Plan: Phase 7 Task 4 — Public Sandbox & Ready-to-Run Examples

## Objective
Provide an `examples/` directory of production-quality, ready-to-run Agent Specs and automated schema validation tests as specified in `docs/SPEC.md § 6`.

## Scope of Changes
1. **`examples/lead-researcher.yaml`**:
   - Production-ready B2B Lead Enrichment agent spec.
   - Autonomy L1 with `web-fetch` and `email-draft` plugins.
   - Guardrails: `pii-redact`, `injection-scan`, `outbound-needs-approval`.
   - Budget: $0.50 per run, $10.00 per day.

2. **`examples/competitor-intel.yaml`**:
   - Competitor pricing and changelog monitor.
   - Autonomy L2 with `web-search` and `web-scrape` plugins.
   - Cron trigger (`0 6 * * *`).
   - Budget: $1.00 per run, $20.00 per day.

3. **`examples/support-triager.yaml`**:
   - Inbound support ticket triage and response drafter.
   - Autonomy L1 with `web-fetch` and `email-draft` plugins.
   - Webhook trigger.
   - Guardrails: `pii-redact`, `schema-valid`.

4. **`examples/README.md`**:
   - Walkthrough of each example agent spec.
   - Execution commands for CLI and UI.
   - Customization guide for startup use cases.

5. **`packages/spec/tests/test_examples_validity.py`**:
   - Automated pytest suite iterating over `examples/*.yaml`.
   - Asserts full compliance with `varistha-spec` Pydantic models.

## Verification
- `python scripts/check_boundaries.py`
- `uv run ruff check .`
- `uv run pyright apps/api`
- `uv run pytest packages/spec/tests/test_examples_validity.py`
- Commit & push to `master` and `main` with green GitHub Actions.
