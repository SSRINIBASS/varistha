"""Guardrail policy execution engine with OpenTelemetry tracing."""

from __future__ import annotations

from typing import Any

from shared.guardrails.interface import (
    PolicyAction,
    PolicyContext,
    PolicyHook,
    PolicyResult,
)
from shared.guardrails.registry import PolicyRegistry, default_policy_registry
from shared.telemetry import (
    VARISTHA_GUARDRAIL_ACTION,
    VARISTHA_GUARDRAIL_HOOK,
    VARISTHA_GUARDRAIL_NAME,
    VARISTHA_GUARDRAIL_PASSED,
    VARISTHA_GUARDRAIL_VIOLATIONS,
    get_tracer,
)


class PolicyEngine:
    """Executes chains of guardrail policies for given lifecycle hooks."""

    def __init__(self, registry: PolicyRegistry | None = None) -> None:
        """Initialize the policy engine with an optional custom registry."""
        self.registry = registry or default_policy_registry
        self.tracer = get_tracer("varistha.guardrails")

    async def evaluate(
        self,
        policy_names: list[str],
        hook: PolicyHook,
        data: Any,
        context: PolicyContext | None = None,
    ) -> PolicyResult:
        """Evaluate a series of named policies against a data payload."""
        if not policy_names:
            return PolicyResult(
                passed=True,
                action=PolicyAction.ALLOW.value,
                modified_data=data,
                violations=[],
            )

        ctx = context or PolicyContext(hook=hook)
        current_data = data
        all_violations: list[str] = []
        is_modified = False

        for name in policy_names:
            policy = self.registry.get(name)
            if policy is None:
                continue

            if hook not in policy.supported_hooks:
                continue

            with self.tracer.start_as_current_span("guardrail.check") as span:
                span.set_attribute(VARISTHA_GUARDRAIL_NAME, policy.name)
                span.set_attribute(VARISTHA_GUARDRAIL_HOOK, hook.value)

                res = await policy.evaluate(current_data, ctx)

                span.set_attribute(VARISTHA_GUARDRAIL_PASSED, res.passed)
                span.set_attribute(VARISTHA_GUARDRAIL_ACTION, res.action)
                if res.violations:
                    span.set_attribute(VARISTHA_GUARDRAIL_VIOLATIONS, "; ".join(res.violations))

            if not res.passed or res.action == PolicyAction.BLOCK.value:
                return res

            if res.action == PolicyAction.REDACT.value and res.modified_data is not None:
                current_data = res.modified_data
                is_modified = True

            if res.violations:
                all_violations.extend(res.violations)

        final_action = PolicyAction.REDACT.value if is_modified else PolicyAction.ALLOW.value
        return PolicyResult(
            passed=True,
            action=final_action,
            modified_data=current_data if is_modified else data,
            violations=all_violations,
        )


default_policy_engine = PolicyEngine()
