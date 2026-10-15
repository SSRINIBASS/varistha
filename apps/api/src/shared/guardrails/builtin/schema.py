"""Schema Validation Guardrail Policy."""

from __future__ import annotations

import json
from typing import Any, ClassVar

from shared.guardrails.interface import (
    BasePolicy,
    PolicyAction,
    PolicyContext,
    PolicyHook,
    PolicyResult,
)


class SchemaValidationPolicy(BasePolicy):
    """Validates model output structure against JSON schema or structural rules."""

    name: str = "schema-valid"
    description: str = (
        "Validates that output data is structured, non-empty, and conforms to expected JSON."
    )
    supported_hooks: ClassVar[set[PolicyHook]] = {PolicyHook.OUTPUT}

    async def evaluate(self, data: Any, context: PolicyContext) -> PolicyResult:
        """Validate output structure."""
        if data is None or (isinstance(data, str) and not data.strip()):
            return PolicyResult(
                passed=False,
                action=PolicyAction.BLOCK.value,
                violations=["Output is empty or null"],
                metadata={"reason": "empty_output"},
            )

        if isinstance(data, dict):
            return PolicyResult(
                passed=True,
                action=PolicyAction.ALLOW.value,
                modified_data=data,
                violations=[],
                metadata={"format": "dict", "keys": list(data.keys())},
            )

        if isinstance(data, str):
            trimmed = data.strip()
            # If formatted like JSON object/list, verify it parses
            if (trimmed.startswith("{") and trimmed.endswith("}")) or (
                trimmed.startswith("[") and trimmed.endswith("]")
            ):
                try:
                    parsed = json.loads(trimmed)
                    return PolicyResult(
                        passed=True,
                        action=PolicyAction.ALLOW.value,
                        modified_data=parsed,
                        violations=[],
                        metadata={"format": "parsed_json"},
                    )
                except json.JSONDecodeError as err:
                    return PolicyResult(
                        passed=False,
                        action=PolicyAction.BLOCK.value,
                        violations=[f"Malformed JSON output: {err.msg} at line {err.lineno}"],
                        metadata={"reason": "json_decode_error"},
                    )

        return PolicyResult(
            passed=True,
            action=PolicyAction.ALLOW.value,
            modified_data=data,
            violations=[],
            metadata={"format": "text"},
        )
