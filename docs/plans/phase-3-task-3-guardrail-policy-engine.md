# Plan: Phase 3, Task 3 — Guardrail Policy Engine & Middleware

## Context & Objectives
Per `docs/SPEC.md § 3.1, § 3.3, § 3.4, § 5` and `AGENTS.md` Security Rules:
- All content fetched from the web, email, or users is **untrusted data**.
- Tool permissions, rate limits, and approval requirements must be enforced in code **outside the model**.
- Guardrail rules are declared in the Agent Spec under `spec.guardrails`:
  - `input`: e.g. `[pii-redact, injection-scan]`
  - `output`: e.g. `[schema-valid, no-unverified-claims]`
  - `tools`: e.g. `[outbound-needs-approval, rate-limit-50-per-day]`
- Every guardrail check must emit an OpenTelemetry trace span with semantic conventions in the `varistha.*` namespace (`guardrail.check`).
- Never log secrets or unredacted PII to telemetry.

## Scope & Components

### 1. Guardrail Core Architecture (`apps/api/src/governance/policies/`)
- `interface.py`:
  - `PolicyHook` enum: `INPUT`, `OUTPUT`, `TOOL_CALL`.
  - `PolicyResult`:
    - `passed: bool`
    - `modified_data: Any | None` (e.g. redacted string/dict)
    - `violations: list[str]`
    - `metadata: dict[str, Any]`
  - `BasePolicy` abstract class with `evaluate(data: Any, context: PolicyContext) -> PolicyResult`.
- `builtin/`:
  - `pii.py` (`PIIRedactionPolicy`, identifier `pii-redact`):
    - Identifies emails, phone numbers, credit card numbers (Luhn check), SSNs, bearer tokens / API keys, and IPv4 addresses.
    - Replaces matches with semantic tokens (`[REDACTED_EMAIL]`, `[REDACTED_PHONE]`, `[REDACTED_KEY]`).
  - `injection.py` (`PromptInjectionPolicy`, identifier `injection-scan`):
    - Multi-vector injection scanner:
      - System instruction overrides ("ignore previous instructions", "disregard system prompt", "you are now in DAN mode").
      - Role-switch / delimiter hijacking (`### Instruction:`, `<system>`, `[INST]`).
      - Exfiltration patterns (markdown image exfiltration `![exfil](https://...$secret)`).
    - Configurable sensitivity (`strict` vs `permissive`).
  - `schema.py` (`SchemaValidationPolicy`, identifier `schema-valid`):
    - Validates JSON output structure against expected schemas.
- `engine.py` (`PolicyEngine`):
  - Resolves policy names from `spec.guardrails`.
  - Executes sequential checks per hook.
  - Emits OpenTelemetry span `guardrail.check` with attributes:
    - `varistha.guardrail.name`: policy name
    - `varistha.guardrail.hook`: `input` | `output` | `tool_call`
    - `varistha.guardrail.passed`: bool
    - `varistha.guardrail.violations`: list of strings
- `registry.py` (`PolicyRegistry`):
  - Catalog of registered policies with metadata and hook targets.

### 2. Runtime Interception Hooking (`apps/api/src/runtime/`)
- In `runtime/service.py`:
  - Pre-flight input evaluation: Run `INPUT` policies on incoming task payload before model dispatch.
  - If injection or hard violation detected: abort run with `RunStatus.FAILED` and explicit `PolicyViolationError`.
  - If PII redaction policy enabled: pass redacted input to execution.
- In `runtime/adapter.py`:
  - Untrusted data hook: When tools (like `web-fetch`) return untrusted content, run injection and PII scanners before feeding back into model messages.
  - Output evaluation: Run `OUTPUT` policies on final model response before persisting run result.

### 3. REST API (`apps/api/src/governance/policies/`)
- `GET /api/v1/policies`: List available policies, supported hooks, and descriptions.
- `POST /api/v1/policies/test`: Interactive endpoint for operators to test policies with arbitrary text payloads.

### 4. CLI Commands (`packages/cli/src/varistha_cli/`)
- `varistha policies list`: Formatted table of registered guardrails.
- `varistha policies test <policy_name> --input "<text>"`: Quick CLI test for guardrail evaluation.

### 5. Architectural Guardrails
- **Bounded Context**: Zero imports from `runtime` inside `governance/policies/`.
- **Pure Python Core**: No external heavy ML dependencies; deterministic regex, tokenizers, and schema validators.
- **Coverage**: ≥ 80% coverage per module.

## Files to Create / Touch
- `apps/api/src/governance/policies/__init__.py`
- `apps/api/src/governance/policies/interface.py`
- `apps/api/src/governance/policies/builtin/pii.py`
- `apps/api/src/governance/policies/builtin/injection.py`
- `apps/api/src/governance/policies/builtin/schema.py`
- `apps/api/src/governance/policies/registry.py`
- `apps/api/src/governance/policies/engine.py`
- `apps/api/src/governance/policies/schemas.py`
- `apps/api/src/governance/policies/router.py`
- `apps/api/src/governance/router.py` (mount policies router)
- `apps/api/src/runtime/service.py` (integrate guardrail hooks)
- `apps/api/src/runtime/adapter.py` (hook untrusted data & output)
- `packages/cli/src/varistha_cli/commands/policies_cmd.py`
- `packages/cli/src/varistha_cli/client.py` & `display.py`
- `apps/api/src/governance/tests/test_policies_*.py`
- `apps/api/src/runtime/tests/test_runtime_guardrails.py`
- `packages/cli/tests/test_policies_cli.py`
