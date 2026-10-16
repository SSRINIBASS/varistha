# Plan: Phase 7 Task 5 — Launch Playbook & Public Roadmap

## Objective
Author the comprehensive launch playbook and public project roadmap for Varistha v0.1.0 public release as specified in `docs/SPEC.md § 6`.

## Scope of Changes
1. **`docs/launch/launch-playbook.md`**:
   - Narrative & Positioning: Leading with lifecycle governance, approvals, and runaway budget controls rather than vague agent hype.
   - Show HN Launch Copy: Hook, problem statement, architecture breakdown, live try command, and technical trade-off decisions.
   - Subreddit Copies: Tailored for `r/selfhosted` (Docker Compose, zero mandatory SaaS, privacy) and `r/LocalLLaMA` (local model inference via Ollama / vLLM, private IP SSRF shields).
   - Product Hunt Kit: Tagline, descriptions, maker comment, and feature badges.
   - Social Media Threads: X (Twitter) and LinkedIn threads emphasizing outside-the-model guardrail enforcement and side-by-side diff approvals.
   - Community Feedback Protocol: GitHub Discussions setup, issue labeling, and contributor onboarding.

2. **`docs/ROADMAP.md`**:
   - Short-term (v0.2.0): Hatchet / Temporal distributed workflow adapter, Slack & Discord notification plugins.
   - Medium-term (v0.3.0): Production Helm chart, eval dataset generation from human edit diffs, native OAuth2/OIDC integration.
   - Long-term (v1.0.0): Enterprise multi-tenant isolation, automated red-teaming harnesses.

3. **`apps/api/src/shared/tests/test_launch_assets.py`**:
   - Automated pytest suite verifying presence, structure, and integrity of launch documentation and roadmap.

## Verification
- `python scripts/check_boundaries.py`
- `uv run ruff check .`
- `uv run pyright apps/api`
- `uv run pytest apps/api/src/shared/tests/test_launch_assets.py`
- Commit & push to `master` and `main` with green GitHub Actions.
