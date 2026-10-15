# Guide: Time-Tied Checkpoint & Phase Gate Protocol

## 1. Purpose

The Checkpoint Protocol guarantees that project progress is rigorously recorded, time-stamped, and verifiable against git history. It ensures no phase is declared complete without meeting its documented exit criteria, and that every task has an auditable record of verification evidence.

---

## 2. Checkpoint Types

### A. Phase Completion Checkpoint
Written when all exit criteria of a major phase (Phase 0 through Phase 7) are satisfied.
- **Location**: `docs/checkpoints/YYYY-MM-DD-phase-N-<name>.md`
- **Git Tag**: Mandatory annotated git tag `phase-N-complete` (e.g. `git tag -a phase-0-complete <commit> -m "Tag Phase 0 complete"`).
- **Gate**: Requires code review passes, ≥ 80% test coverage, and Project Reviewer sign-off.

### B. Task Milestone Checkpoint
Written at the completion of significant PR-sized tasks within an active phase (e.g. Phase 1 Task 1, Phase 1 Task 2).
- **Location**: `docs/checkpoints/YYYY-MM-DD-phase-N-task-M-<name>.md`
- **Git Link**: Tied directly to the task commit hash.

---

## 3. Checkpoint Document Standard Structure

Every checkpoint document MUST contain the following sections:

```markdown
# [Phase / Milestone] Checkpoint: <Title>

- **Phase**: <Phase Number and Name>
- **Task**: <Task Number and Title, if applicable>
- **Status**: PASSED / FAILED / IN_PROGRESS
- **Timestamp**: YYYY-MM-DDTHH:MM:SS+TZ (ISO-8601 local/UTC time)
- **Git Commit**: <Full or 7-character commit SHA>
- **Git Tag**: <e.g. phase-0-complete, if phase completion>
- **Reference Spec**: <Specific section in docs/SPEC.md>

---

## 1. Exit Criteria / Implemented Capabilities
<Table or list comparing SPEC requirements to implemented capabilities>

## 2. Test & Quality Metrics
- Total Tests: <N> passing
- Coverage: <N>% (target ≥ 80%)
- Linter: ruff clean
- Type-check: pyright clean
- Architecture boundaries: check_boundaries.py clean

## 3. Artifact Manifest
<List of created or modified source files, tests, and ADRs>

## 4. Known Gaps & Next Steps
<Clear statement of remaining work and immediate next task>
```

---

## 4. Phase Gate Protocol Rules

Per `AGENTS.md`, **never advance to the next phase until:**
1. All exit criteria for the current phase in `docs/SPEC.md § 5` are met.
2. Automated checks pass (`ruff`, `pyright`, `pytest` with ≥ 80% coverage per module, `bandit`, `pip-audit`).
3. Project Reviewer has issued `PASS` or `PASS WITH NOTES`.
4. Git tag `phase-N-complete` is created on the release commit.
5. Checkpoint document is written and committed in `docs/checkpoints/`.
