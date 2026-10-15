# ADR 0011: Spec Diffing Engine and Breaking Change Classification

## Status
Accepted

## Context
Per `docs/SPEC.md § 4.4` ("Show diffs, not blobs... A version change shows a spec diff") and `§ 5` ("Spec diffing engine detects breaking vs non-breaking changes across any two versions"), operators and control planes require fine-grained visibility into configuration changes when updating agent specifications.

Without automated change classification, modifying an agent specification could silently weaken security policies (e.g. removing guardrails), escalate autonomy without oversight (e.g. L1 to L2), or alter primary models causing reasoning degradation. Operators need a deterministic, structured diffing engine that operates on immutable spec versions, flags breaking changes, and integrates with the API, UI, and CLI.

## Decision

### 1. Pure Diffing Engine in `packages/spec` (`diff.py`)
- Implemented `diff_specs(old_spec, new_spec) -> SpecDiff` as a pure, dependency-isolated engine inside `packages/spec`.
- Input coercion accepts either validated `AgentSpec` instances or raw dictionaries (validated via `validate_spec()`).
- Returns structured Pydantic models:
  - `DiffEntry`: field path, change type (`added`, `removed`, `modified`), old value, new value, `is_breaking: bool`, `breaking_reason: str | None`, and human-readable description.
  - `SpecDiff`: `from_version`, `to_version`, `has_changes`, `has_breaking_changes`, summary counts (`total`, `added`, `removed`, `modified`, `breaking`), and detailed entry lists.

### 2. Breaking vs Non-Breaking Change Taxonomy
The engine enforces deterministic rules grounded in safety, security, and runtime predictability:
- **Autonomy Escalation (Breaking):** Upgrading autonomy (e.g. L0/L1 → L2/L3) expands unsupervised tool execution permissions. Downgrading autonomy is safe.
- **Guardrail Removal (Breaking):** Removing any policy from `input`, `output`, or `tools` guardrails weakens the security perimeter. Adding guardrails is safe.
- **Primary Model Change (Breaking):** Altering `spec.model.primary` can disrupt prompt compatibility, formatting, and behavioral reasoning. Changing fallback models is safe.
- **Plugin Removal or Disabling (Breaking):** Removing a plugin or toggling `enabled: True -> False` breaks prompt workflows expecting tool availability. Adding or enabling plugins is safe.
- **Budget Tightening or Removal (Breaking):** Lowering `max_usd_per_run` or `max_usd_per_day` can cause in-flight or production workflows to fail unexpectedly. Removing budgets entirely removes financial bounds. Increasing budget limits is safe.
- **Trigger Removal (Breaking):** Removing an active trigger (e.g. scheduled cron or manual trigger) halts automated workflows. Adding triggers or adjusting cron schedules is safe/modified.
- **Eval Threshold Tightening or Removal (Breaking):** Removing an eval suite eliminates quality gates; raising `min_pass_rate` tightens promotion requirements.
- **Agent Slug Change (Breaking):** Agent identifier names cannot diverge between versions.
- **Metadata and Instruction Updates (Non-Breaking / Modified):** Owner reassignment, lifecycle stage transitions, prompt instruction updates, and semver version increments are categorized as non-breaking modifications.

### 3. API Surface in `apps/api/src/registry/`
- `GET /api/v1/agents/{id_or_name}/versions/{v1}/diff/{v2}`: Compares two published immutable version snapshots from the database.
- `POST /api/v1/agents/{id_or_name}/diff`: Previews field-level changes between an uncommitted candidate spec and an active base version (enabling pre-flight checks in CLI and UI).

### 4. CLI Command (`varistha diff`)
- `varistha diff <agent-name> <v1> <v2>`: Fetches and displays version-to-version diffs.
- `varistha diff -f <agent.yaml> [--base-version <v>]`: Validates and diffs local spec against the control plane before publishing.
- `--strict` flag: Exits with code 1 if breaking changes are detected, serving as an automated CI/CD acceptance gate.
- Rendered with `rich` panels, color-coded badges (`+ ADDED`, `- REMOVED`, `~ MODIFIED`), and bold red alerts for breaking changes.

## Consequences

### Positive
- Operators and CI pipelines have verifiable visibility into what changed between versions before promoting or running agents.
- Security and autonomy escalations are surfaced immediately as breaking changes.
- Pure spec package keeps diffing completely decoupled from database models and runtime logic.

### Negative
- Field additions to `AgentSpec` require corresponding mapping in `diff.py`.
