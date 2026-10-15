# Plan: Phase 2, Task 2 — Spec Diffing Engine

> **For Agent:** Implement Phase 2 Task 2 per `AGENTS.md` and `docs/SPEC.md § 3.2, § 4.4, § 5`.

**Goal:** Implement a deterministic, structured Spec Diffing Engine in `packages/spec` that compares any two agent specification versions, detects fine-grained changes across all configuration blocks, categorizes changes as **breaking** vs **non-breaking**, and exposes diffs through API endpoints and the CLI.

---

## 1. Context & Motivation

Per `docs/SPEC.md § 5` (Phase 2 exit criteria):
- *"Spec diffing engine detects breaking vs non-breaking changes across any two versions."*
- Per § 4.4 (UI and design principles): *"Show diffs, not blobs... A version change shows a spec diff."*

When an AI employee's spec is updated (e.g. changing autonomy from L1 to L2, dropping a safety guardrail, swapping a model, or lowering a budget), operators need immediate, verifiable visibility into what changed and whether the change alters safety, risk, or execution reliability.

---

## 2. Breaking vs Non-Breaking Taxonomy

A change is classified as **breaking** if it weakens safety guardrails, expands operational autonomy, removes required capabilities, or risks breaking existing workloads:

| Area | Change | Classification | Rationale |
| :--- | :--- | :--- | :--- |
| **Autonomy** | Escalated (e.g. L0/L1 → L2/L3) | **Breaking** | Bypasses human approval gates for outbound/autonomous actions. |
| **Autonomy** | De-escalated (e.g. L3 → L1) | Non-breaking | Increases safety/human oversight. |
| **Guardrails** | Rule removed from `input`, `output`, or `tools` | **Breaking** | Weakens security policies (e.g., removing `pii-redact` or `injection-scan`). |
| **Guardrails** | Rule added to `input`, `output`, or `tools` | Non-breaking | Tightens security constraints. |
| **Model** | Primary model changed | **Breaking** | Model swap may introduce behavioral divergence, prompt incompatibility, or latency regression. |
| **Model** | Fallback model added / changed | Non-breaking | Redundancy improvement without altering primary execution path. |
| **Plugins** | Plugin removed from spec | **Breaking** | Prompts and workflows depending on tool execution may fail. |
| **Plugins** | Plugin toggled from `enabled: True` to `False` | **Breaking** | Disables an active capability. |
| **Plugins** | Plugin added or toggled `False` → `True` | Non-breaking | Adds new capability without breaking existing behavior. |
| **Budget** | `max_usd_per_run` or `max_usd_per_day` reduced | **Breaking** | Previously valid runs may now trigger hard budget cutoffs. |
| **Budget** | Budget limits increased | Non-breaking | Permits higher headroom. |
| **Budget** | Budget removed entirely | **Breaking** | Unconstrained spend risk. |
| **Triggers** | Active trigger removed or disabled | **Breaking** | Automated scheduled/webhook execution halts. |
| **Triggers** | Trigger added or cron modified | Non-breaking / Modified | Adds schedule or updates cadence. |
| **Evals** | Eval suite removed | **Breaking** | Removes automated promotion validation. |
| **Evals** | `min_pass_rate` increased | **Breaking** | Raises promotion acceptance gate. |
| **Instructions** | Instruction text / file path updated | Non-breaking (Modified) | Behavior modified, but non-breaking schema. |
| **Metadata** | `owner`, `stage`, `version` changed | Non-breaking | Standard lifecycle & administrative tracking. |

---

## 3. Architecture & Data Structures (`packages/spec`)

### Models (`packages/spec/src/diff.py`)

```python
class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"


class DiffEntry(BaseModel):
    field: str  # e.g. "spec.autonomy", "spec.guardrails.input", "spec.model.primary"
    change_type: ChangeType  # added | removed | modified
    old_value: Any  # previous value (None if added)
    new_value: Any  # new value (None if removed)
    is_breaking: bool  # True if categorized as breaking
    breaking_reason: str | None  # Explanation of why this change is breaking
    description: str  # Human-readable summary of the delta


class SpecDiff(BaseModel):
    from_version: str | None  # Base version string
    to_version: str | None  # Target version string
    has_changes: bool  # True if any entry exists
    has_breaking_changes: bool  # True if any entry is_breaking
    summary: dict[str, int]  # {"total": N, "added": N, "removed": N, "modified": N, "breaking": N}
    entries: list[DiffEntry]  # All detailed field diffs
    breaking_entries: list[DiffEntry]  # Filtered convenience view of breaking changes
```

### Core Function

```python
def diff_specs(
    old_spec: AgentSpec | dict[str, Any],
    new_spec: AgentSpec | dict[str, Any],
) -> SpecDiff:
    """Compare two agent specs and return a structured diff with breaking change detection."""
```

---

## 4. API Endpoints (`apps/api/src/registry/`)

1. **Compare Published Versions:**
   `GET /api/v1/agents/{id_or_name}/versions/{v1}/diff/{v2}`
   - Resolves agent by UUID or name.
   - Fetches snapshot specs for versions `v1` and `v2`.
   - Runs `diff_specs` and returns `SpecDiffResponse`.

2. **Preview Diff (Dry-Run Against Active Spec):**
   `POST /api/v1/agents/{id_or_name}/diff`
   - Body: `SpecDiffRequest(spec: dict[str, Any], base_version: str | None = None)`
   - Compares candidate spec against `base_version` (or current active version if None).
   - Allows CLI and UI to display breaking change warnings before applying or publishing.

---

## 5. CLI Command (`packages/cli/src/varistha_cli/`)

- Command: `varistha diff <agent-id-or-name> <v1> <v2>`
  - Fetches and displays version-to-version diff.
- Command: `varistha diff -f agent.yaml [--base-version <v>]`
  - Validates local YAML and diffs against currently published remote version.
- Rich display in `display.py`:
  - Panel with breaking change alert if `has_breaking_changes` is true.
  - Formatted table with color-coded badges:
    - `ADDED` (green)
    - `REMOVED` (red)
    - `MODIFIED` (yellow)
    - `[BREAKING]` badge with bold red explanation.

---

## 6. Files to Touch

### New Files
1. `packages/spec/src/diff.py` — Core diffing engine and breaking-change rules.
2. `packages/spec/tests/test_diff.py` — Unit tests for diffing across all spec components.
3. `apps/api/src/registry/tests/test_diff_api.py` — Integration tests for diff endpoints.
4. `packages/cli/src/varistha_cli/commands/diff_cmd.py` — CLI `diff` command.
5. `packages/cli/tests/test_diff_cmd.py` — Tests for CLI diff command.
6. `docs/adr/0011-spec-diffing-engine-and-breaking-changes.md` — ADR for diffing and breaking change semantics.
7. `docs/plans/phase-2-task-2-spec-diff.md` — This plan document.

### Modified Files
1. `packages/spec/src/__init__.py` — Export `diff_specs`, `SpecDiff`, `DiffEntry`, `ChangeType`.
2. `apps/api/src/registry/schemas.py` — Pydantic schemas for diff endpoints.
3. `apps/api/src/registry/service.py` — Service helpers to fetch specs and compute diff.
4. `apps/api/src/registry/router.py` — Mount diff endpoints.
5. `packages/cli/src/varistha_cli/client.py` — Add `get_version_diff()` and `preview_spec_diff()`.
6. `packages/cli/src/varistha_cli/display.py` — Add `print_spec_diff()`.
7. `packages/cli/src/varistha_cli/main.py` — Register `diff_cmd`.
8. `CHANGELOG.md` — Record changes.

---

## 7. Step-by-Step Execution Order

1. **Step 1: Core Engine (`packages/spec`)**
   - Implement `packages/spec/src/diff.py`.
   - Update `packages/spec/src/__init__.py`.
   - Write comprehensive tests in `packages/spec/tests/test_diff.py`.
   - Verify `uv run pytest packages/spec/tests/`.

2. **Step 2: Service & API Endpoints (`apps/api`)**
   - Add schemas in `apps/api/src/registry/schemas.py`.
   - Add service functions in `apps/api/src/registry/service.py`.
   - Add routes in `apps/api/src/registry/router.py`.
   - Write API tests in `apps/api/src/registry/tests/test_diff_api.py`.
   - Verify `uv run pytest apps/api/src/registry/tests/`.

3. **Step 3: CLI Diff Command (`packages/cli`)**
   - Add client methods to `packages/cli/src/varistha_cli/client.py`.
   - Add rich diff renderer in `packages/cli/src/varistha_cli/display.py`.
   - Implement `packages/cli/src/varistha_cli/commands/diff_cmd.py`.
   - Wire command in `packages/cli/src/varistha_cli/main.py`.
   - Write tests in `packages/cli/tests/test_diff_cmd.py`.

4. **Step 4: Quality Gate & Documentation**
   - Run full monorepo suite: `pytest`, `ruff check`, `ruff format --check`, `pyright`, `check_boundaries.py`, `bandit`.
   - Create ADR `0011-spec-diffing-engine-and-breaking-changes.md`.
   - Update `CHANGELOG.md`.
