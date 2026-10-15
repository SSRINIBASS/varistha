# ADR 0015: Guardrail Policy Engine, PII Redaction, and Prompt Injection Scanner

## Status
Accepted

## Context
Per `docs/SPEC.md § 3.1` (Autonomy Levels L0-L4), `§ 3.3` (Governance & Guardrail Policies), `§ 3.4` (OpenTelemetry Tracing), and `§ 5` (Phase 3 Milestones), autonomous AI agents must operate under deterministic, outside-the-model safety constraints.

Specifically:
1. All content fetched from the web, email, or user input is **untrusted data**.
2. Guardrail policies, input validation, PII redaction, and prompt injection scanning must run in deterministic code **outside the model**, preventing untrusted data from modifying system prompts or executing malicious instructions.
3. Every Agent Spec can declare guardrails in `spec.guardrails.input`, `spec.guardrails.output`, and `spec.guardrails.tools`.
4. Pre-flight input guardrails must run before runtime invocation, rejecting injection attacks with HTTP 422 Unprocessable Content (`PolicyViolationError`) or sanitizing sensitive PII before execution.
5. Post-execution output guardrails must validate generated content before finalizing agent output.
6. OpenTelemetry traces must record a `guardrail.check` span for every policy evaluation with semantic attributes:
   - `varistha.guardrail.name`
   - `varistha.guardrail.hook`
   - `varistha.guardrail.passed`
   - `varistha.guardrail.action`
   - `varistha.guardrail.violations`

## Decision

### 1. Shared Guardrails Kernel (`apps/api/src/shared/guardrails/`)
To satisfy architectural boundary rules (`scripts/check_boundaries.py`) without introducing cross-context dependencies between `runtime` and `governance`, the core evaluation interfaces and built-in policies are housed in the shared kernel:
- **`interface.py`**:
  - `PolicyHook`: Enum with values `input`, `output`, `tools`.
  - `PolicyAction`: Enum with values `allow`, `redact`, `block`.
  - `PolicyResult`: Structured outcome containing `passed`, `action`, `modified_data`, `violations`, and `metadata`.
  - `PolicyContext`: Execution metadata (`agent_id`, `agent_name`, `hook`, `metadata`).
  - `BasePolicy`: Abstract base class enforcing `name`, `description`, `supported_hooks`, and async `evaluate(data, context)`.
- **`registry.py`**:
  - `PolicyRegistry`: Singleton / factory managing policy registration, lookups, and discovery.
  - Automatically registers default built-in policies.
- **`engine.py`**:
  - `PolicyEngine`: Orchestrates sequential policy evaluation for a target hook.
  - Redaction chaining: Passes sanitized data down the pipeline.
  - Short-circuit on block: Halts immediately if any policy emits `block`.
  - OpenTelemetry integration: Wraps each evaluation in a `guardrail.check` span.
- **Built-in Policies (`shared/guardrails/builtin/`)**:
  - `pii-redact` (`PIIRedactionPolicy`): Redacts emails, phone numbers, credit cards (with Luhn algorithm verification), SSNs, API keys / bearer tokens, and IPv4 addresses across text and nested JSON structures.
  - `injection-scan` (`PromptInjectionPolicy`): Detects prompt injection, instruction overrides, system delimiter hijacking (`<system>`, `[INST]`, `### Instruction:`), and image markdown token exfiltration.
  - `schema-valid` (`SchemaValidationPolicy`): Verifies structured JSON or dictionary output conformity.
  - `no-unverified-claims` (`NoUnverifiedClaimsPolicy`): Flags ungrounded absolute guarantees.

### 2. Runtime Interception Middleware
- **Input Guardrails (`apps/api/src/runtime/service.py`)**:
  - In `trigger_agent_run()`, pre-flight evaluates `spec.guardrails.input` within `capture_run_spans(run_id)`.
  - If blocked, raises `PolicyViolationError` (mapped to HTTP 422 in `runtime/router.py`) without triggering runtime or executing model calls.
  - If redacted, updates `effective_input_data` and executes the agent with sanitized inputs.
- **Output Guardrails (`apps/api/src/runtime/adapter.py` and `apps/api/src/runtime/mock.py`)**:
  - Evaluates `spec.guardrails.output` post-execution.
  - If output fails schema or safety checks, updates run status to `failed` and records violations.

### 3. Governance Policy Management API (`apps/api/src/governance/policies/`)
Mounted under `/api/v1/policies`:
- `GET /api/v1/policies`: Lists all registered guardrail policies with their supported hook points and descriptions.
- `POST /api/v1/policies/test`: Evaluates any policy against arbitrary payloads for interactive verification and CI/CD validation.

### 4. CLI Inspection and Testing (`packages/cli/`)
- Added `varistha policies` command group:
  - `varistha policies list [--json]`: Renders a Rich table of registered policies.
  - `varistha policies test <policy_name> -i <text> [--hook <input|output|tools>] [--json]`: Tests a policy against sample input and renders a detailed outcome panel with redactions or violation alerts.

## Consequences
- **Security**: Outside-the-model deterministic enforcement prevents untrusted inputs from reaching LLM backends and ensures PII is never stored or transmitted unredacted.
- **Observability**: Full traceability with `guardrail.check` spans in OpenTelemetry for governance audits.
- **Modularity**: New custom policies can be registered without touching core runtime or API routing logic.
- **Architectural Cleanliness**: Zero cross-context imports between `runtime` and `governance`.
