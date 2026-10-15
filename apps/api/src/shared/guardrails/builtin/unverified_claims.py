"""No Unverified Claims Output Guardrail Policy."""

from __future__ import annotations

import re
from typing import Any, ClassVar

from shared.guardrails.interface import (
    BasePolicy,
    PolicyAction,
    PolicyContext,
    PolicyHook,
    PolicyResult,
)

_UNVERIFIED_CLAIM_PATTERNS = [
    re.compile(r"(?i)\b100%\s+guaranteed\s+(?:returns?|profit|success)\b"),
    re.compile(r"(?i)\brisk-?free\s+(?:investment|wealth|returns?)\b"),
    re.compile(r"(?i)\bguaranteed\s+(?:cure|treatment)\s+for\s+all\b"),
    re.compile(r"(?i)\bfoolproof\s+system\s+to\s+get\s+rich\b"),
]


class NoUnverifiedClaimsPolicy(BasePolicy):
    """Detects high-risk ungrounded claims or hallucinated guarantees in model outputs."""

    name: str = "no-unverified-claims"
    description: str = (
        "Flags unsubstantiated absolute claims (guaranteed returns, universal cures)."
    )
    supported_hooks: ClassVar[set[PolicyHook]] = {PolicyHook.OUTPUT}

    def _scan_text(self, text: str) -> list[str]:
        violations: list[str] = []
        for p in _UNVERIFIED_CLAIM_PATTERNS:
            if p.search(text):
                violations.append(f"Unverified high-risk assertion pattern: '{p.pattern}'")
        return violations

    def _scan_recursive(self, item: Any, violations: list[str]) -> None:
        if isinstance(item, str):
            violations.extend(self._scan_text(item))
        elif isinstance(item, dict):
            for v in item.values():
                self._scan_recursive(v, violations)
        elif isinstance(item, list):
            for v in item:
                self._scan_recursive(v, violations)

    async def evaluate(self, data: Any, context: PolicyContext) -> PolicyResult:
        """Scan output for unverified assertions."""
        violations: list[str] = []
        self._scan_recursive(data, violations)

        if violations:
            return PolicyResult(
                passed=False,
                action=PolicyAction.BLOCK.value,
                modified_data=None,
                violations=violations,
                metadata={"blocked_by": self.name, "violation_count": len(violations)},
            )

        return PolicyResult(
            passed=True,
            action=PolicyAction.ALLOW.value,
            modified_data=data,
            violations=[],
            metadata={"status": "clean"},
        )
