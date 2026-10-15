# Plan: Phase 1, Task 1 — Agent Spec Models & Validator

## Goal
Implement declarative Agent Spec Pydantic v2 models, YAML and dict validators, JSON Schema export, and the canonical test fixture from `docs/SPEC.md § 3.4`.

## Scope
- `packages/spec/src/models.py`: Pydantic models with `extra="forbid"`, slug validation, semver regex, autonomy levels `Literal["L0", "L1", "L2", "L3"]`.
- `packages/spec/src/validator.py`: `validate_spec` and `validate_spec_yaml` wrapping errors into `SpecValidationError`.
- `packages/spec/src/schema.py`: CLI generator writing `schema.json`.
- `packages/spec/tests/fixtures/lead-researcher.yaml`: Reference fixture.
- `packages/spec/tests/test_models.py` and `packages/spec/tests/test_validator.py`: Comprehensive test suite.
