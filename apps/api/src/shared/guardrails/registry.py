"""Policy registry for managing installed guardrail policies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.guardrails.builtin import (
    NoUnverifiedClaimsPolicy,
    PIIRedactionPolicy,
    PromptInjectionPolicy,
    SchemaValidationPolicy,
)

if TYPE_CHECKING:
    from shared.guardrails.interface import BasePolicy


class PolicyRegistry:
    """Registry maintaining available guardrail policies."""

    def __init__(self) -> None:
        """Initialize the policy registry with default built-in policies."""
        self._policies: dict[str, BasePolicy] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default built-in platform policies."""
        self.register(PIIRedactionPolicy())
        self.register(PromptInjectionPolicy())
        self.register(SchemaValidationPolicy())
        self.register(NoUnverifiedClaimsPolicy())

    def register(self, policy: BasePolicy) -> None:
        """Register a policy instance."""
        self._policies[policy.name] = policy

    def get(self, name: str) -> BasePolicy | None:
        """Retrieve a policy by its unique identifier."""
        return self._policies.get(name)

    def list_policies(self) -> list[BasePolicy]:
        """Return all registered policy instances."""
        return list(self._policies.values())

    def reset(self) -> None:
        """Reset registry back to default built-ins."""
        self._policies.clear()
        self._register_defaults()


default_policy_registry = PolicyRegistry()
