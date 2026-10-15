# Guide: Agent Spec Authoring & Validation

## 1. Overview

The **Agent Spec** is the declarative definition of an AI Employee in Varistha. It specifies:
- Identity, ownership, version, and lifecycle stage.
- Models (primary and fallback via LiteLLM).
- Instructions (inline prompt or relative file path).
- Attached MCP plugins and scopes.
- Autonomy level (`L0`, `L1`, `L2`, `L3`).
- Guardrails (input, output, and tool policies).
- Budget limits (cost per run and cost per day in USD).
- Triggers (manual, schedule cron, webhook).
- Eval suite configuration and minimum pass rate.

---

## 2. Canonical Specification Example

```yaml
apiVersion: varistha/v1
kind: Agent
metadata:
  name: lead-researcher
  owner: founder@example.com
  stage: prototype
  version: 0.3.0
spec:
  role: Find and qualify B2B leads matching our ICP, draft a personalised first touch.
  model:
    primary: gpt-4o
    fallback: local/ollama-model
  instructions: ./prompts/lead-researcher.md
  plugins:
    - name: web-fetch
      enabled: true
    - name: web-search
      enabled: true
    - name: email-draft
      enabled: true
    - name: email-send
      enabled: false
  autonomy: L1
  guardrails:
    input: [pii-redact, injection-scan]
    output: [schema-valid, no-unverified-claims]
    tools: [outbound-needs-approval, rate-limit-50-per-day]
  budget:
    max_usd_per_run: 0.50
    max_usd_per_day: 10
  triggers:
    - type: schedule
      cron: "0 9 * * 1-5"
    - type: manual
  evals:
    suite: ./evals/lead-researcher.yaml
    min_pass_rate: 0.85
```

---

## 3. Validation in Code

Validate raw dictionaries or YAML strings using `packages/spec`:

```python
from spec import validate_spec, validate_spec_yaml, SpecValidationError

# From YAML
try:
    spec = validate_spec_yaml(yaml_content)
    print(f"Validated agent: {spec.metadata.name} v{spec.metadata.version}")
except SpecValidationError as e:
    for err in e.errors:
        print(f"Validation error: {err}")
```

---

## 4. JSON Schema for Editor Tooling

A JSON Schema is available at [`packages/spec/src/schema.json`](file:///c:/Users/srini/OneDrive/Documents/Amygdylla/VARISTHA/packages/spec/src/schema.json).
In VS Code or Cursor, associate YAML files with the schema in `.vscode/settings.json`:

```json
{
  "yaml.schemas": {
    "./packages/spec/src/schema.json": ["*agent*.yaml", "*agent*.yml"]
  }
}
```
