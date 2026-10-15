# Milestone Checkpoint: Phase 1, Task 1 — Agent Spec Models & Validator

- **Phase**: Phase 1 — Walking Skeleton (Week 2-3)
- **Task**: Task 1 — Agent Spec JSON Schema, Pydantic models, validator, and test fixtures
- **Status**: PASSED
- **Timestamp**: 2026-10-15T12:16:54+05:30
- **Git Commit**: `7527f95`
- **Reference Spec**: `docs/SPEC.md § 3.4 & § 7.5 Task 1`

---

## 1. Implemented Capabilities

1. **Pydantic v2 Models (`packages/spec/src/models.py`)**:
   - `AgentSpec`, `AgentMetadata`, `AgentSpecBody`, `ModelConfig`, `PluginRef`, `GuardrailsConfig`, `BudgetConfig`, `TriggerConfig`, `EvalConfig`.
   - Strict `model_config = ConfigDict(extra="forbid")` on all models to reject unrecognized keys.
   - Slug regex validation on `metadata.name` and semver regex on `metadata.version`.
   - Autonomy constrained to `Literal["L0", "L1", "L2", "L3"]`.
2. **Validator (`packages/spec/src/validator.py`)**:
   - `validate_spec(raw: dict) -> AgentSpec`
   - `validate_spec_yaml(yaml: str) -> AgentSpec`
   - Maps Pydantic `ValidationError` into `SpecValidationError` with human-readable, location-prefixed messages (`metadata -> name: ...`).
3. **JSON Schema Tooling (`packages/spec/src/schema.py` & `schema.json`)**:
   - Standalone JSON Schema export for IDE YAML auto-completion.
4. **Test Fixture**:
   - `packages/spec/tests/fixtures/lead-researcher.yaml` (canonical reference spec from SPEC.md § 3.4).

---

## 2. Test & Quality Metrics

- **Unit Tests Added**: 25 (18 model tests + 7 validator tests)
- **Cumulative Tests**: 27 passing
- **Test Coverage**: 84.5% on `packages/spec/src` (exceeds ≥ 80% gate)
- **Linter Status**: `ruff check` clean (0 errors)
- **Type Checker Status**: `pyright` strict clean (0 errors)
- **Architectural Decision Record**: `docs/adr/0002-agent-spec-schema.md`
- **Dependencies Added**: `email-validator>=2.1` (MIT license)
