# ADR-0002: Agent Spec Schema Design

**Date:** 2026-10-15
**Status:** Accepted
**Deciders:** Varistha core team

---

## Context

Phase 1, Task 1 requires a canonical, versioned definition of the `varistha/v1 Agent` spec
(described in `docs/SPEC.md § 3.4`).  This definition is the foundation for:

- API request/response validation
- CLI `varistha apply -f agent.yaml` parsing
- Database storage of immutable agent version snapshots
- JSON Schema for editor tooling (VS Code, Cursor YAML extension)

We need to pick a modelling approach and settle several design questions before any
other Phase 1 task can proceed.

---

## Decision

### 1. Pydantic v2 as the sole schema layer

We use **Pydantic v2** (`model_validate`, `model_json_schema`) rather than raw dataclasses,
`attrs`, or `marshmallow`.

**Rationale:**
- FastAPI (the API layer) natively integrates Pydantic v2 — the same model objects become
  OpenAPI request/response schemas with zero extra work.
- `model_json_schema()` generates a valid JSON Schema for editor tooling without a separate
  schema authoring step.
- Pydantic v2 is significantly faster than v1 and has first-class async support.

### 2. `extra="forbid"` on every model

All models use `model_config = ConfigDict(extra="forbid")`.

**Rationale:**
- Agent specs are security-relevant.  Silently ignoring unknown keys (e.g. an attacker
  injecting `bypass_approval: true`) is dangerous.
- Hard failure on unknown fields catches typos early and gives useful error messages.
- This is the strictest default; individual models can relax it later if a use case requires it.

### 3. `instructions` is a plain string, not a resolved path

The `instructions` field accepts either a relative file path (`./prompts/agent.md`) or
inline text.  **File existence is NOT checked at validation time.**

**Rationale:**
- The spec package is a pure data layer with no I/O.  Resolving paths requires knowing the
  working directory, which is a runtime concern.
- An agent spec might be validated in a context where the referenced files are not yet
  present (e.g. inside a CI pipeline or a registry import).
- The runtime adapter (`apps/api/src/runtime/`) is responsible for resolving and loading
  instruction files before agent execution.

This is documented in the field docstring so callers are not surprised.

### 4. Autonomy as a Literal string enum, not an int

Autonomy is `Literal["L0", "L1", "L2", "L3"]` rather than an integer `0-3`.

**Rationale:**
- String literals (`"L1"`) are self-documenting in YAML and log output.
- No arithmetic is performed on autonomy levels in the spec layer; comparisons are always
  equality checks (`autonomy == "L1"`), which work equally well for strings.
- Integers would require a range validator and a lookup table for display; a Literal enum
  does both in one declaration.

### 5. Semver validated with a simple regex, not a library

Version strings are validated against `^\d+\.\d+\.\d+(-[A-Za-z0-9.]+)?(\+[A-Za-z0-9.]+)?$`.

**Rationale:**
- Pulling in `packaging` or `semver` just for version parsing would add a dependency for
  a single field.
- The regex covers the practical cases (major.minor.patch, pre-release suffix,
  build metadata).  Full SemVer 2.0.0 edge cases (multiple pre-release identifiers,
  numeric pre-release comparison) are not needed for agent version strings.

### 6. `SpecValidationError` as a thin wrapper

`SpecValidationError` wraps Pydantic's `ValidationError` and exposes
`errors: list[str]` with location-prefixed human-readable messages.

**Rationale:**
- Callers (CLI, API) should not depend on Pydantic internals.  If we ever swap the
  modelling layer, the exception interface stays stable.
- The location prefix (`metadata -> name: …`) is preserved from Pydantic's own loc tuple
  to help users find the problematic field quickly.

---

## Consequences

- `packages/spec/src/` contains four modules: `models`, `validator`, `schema`, `exceptions`.
  All public symbols are re-exported from `__init__.py`.
- `packages/spec/src/schema.json` is generated and committed; regenerate with
  `uv run python packages/spec/src/schema.py`.
- `packages/spec/pyproject.toml` depends on `pydantic[email]>=2.10` and
  `email-validator>=2.1` (MIT) for `EmailStr` on the `owner` field.
- All other Phase 1 tasks import from `spec.models` and `spec.validator`; they never
  import Pydantic directly for schema concerns.

## Alternatives considered

- **Raw dataclasses**: rejected — no built-in JSON Schema generation or nested validation.
- **`attrs` + `cattrs`**: rejected — less FastAPI integration, extra dependency pair.
- **`marshmallow`**: rejected — no JSON Schema export, separate schema and model classes.
- **Integer autonomy levels**: rejected — less readable in YAML output and log lines.
- **`packaging` library for semver**: rejected — unnecessary dependency for a regex check.
