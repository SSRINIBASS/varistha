"""Starter Agent Spec YAML templates for varistha init."""

from __future__ import annotations


def generate_starter_spec(
    name: str = "my-agent",
    role: str | None = None,
    owner: str = "team@example.com",
    primary_model: str = "gpt-4o-mini",
) -> str:
    """Generate a valid starter Agent Spec YAML string."""
    role_text = role or (
        "Find and qualify B2B leads matching our ICP, draft a personalised first touch."
    )
    # Ensure role is single line or properly formatted
    role_text = " ".join(role_text.strip().splitlines())

    return f"""apiVersion: varistha/v1
kind: Agent
metadata:
  name: {name}
  owner: {owner}
  stage: prototype
  version: 0.1.0
spec:
  role: >
    {role_text}
  model:
    primary: {primary_model}
    fallback: gpt-3.5-turbo
  instructions: |
    Analyze the company profile and domain.
    Extract key executives, current tech stack, and primary value proposition.
    Draft a concise, personalized outreach note.
  plugins:
    - name: web-fetch
      enabled: true
  autonomy: L1
  guardrails:
    input:
      - pii-redact
      - injection-scan
    output:
      - schema-valid
    tools:
      - outbound-needs-approval
  budget:
    max_usd_per_run: 0.50
    max_usd_per_day: 10.00
  triggers:
    - type: manual
"""
