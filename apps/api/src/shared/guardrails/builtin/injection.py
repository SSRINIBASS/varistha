"""Prompt Injection and Adversarial Content Scanner."""

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

_OVERRIDE_PATTERNS = [
    re.compile(
        r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules|guidelines)\b"
    ),
    re.compile(
        r"(?i)\bdisregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|rules|guidelines)\b"
    ),
    re.compile(
        r"(?i)\bforget\s+(?:your\s+|all\s+)?(?:previous|prior|system)\s+(?:instructions|rules|guidelines)\b"
    ),
    re.compile(r"(?i)\bignore\s+(?:your\s+)?system\s+prompt\b"),
    re.compile(r"(?i)\bsystem\s+override\b"),
    re.compile(r"(?i)\byou\s+are\s+now\s+(?:in\s+)?dan\s+mode\b"),
    re.compile(r"(?i)\bdo\s+anything\s+now\b"),
    re.compile(r"(?i)\bact\s+as\s+an\s+unrestricted\s+ai\b"),
    re.compile(r"(?i)\byou\s+have\s+no\s+(?:safety\s+)?restrictions\b"),
    re.compile(r"(?i)\bjailbreak\s+mode\b"),
    re.compile(r"(?i)\bbypass\s+(?:all\s+)?(?:guardrails|safety\s+filters)\b"),
]

_DELIMITER_PATTERNS = [
    re.compile(r"(?i)<\s*/?\s*system\s*>"),
    re.compile(r"(?i)\[/?INST\]"),
    re.compile(r"(?i)<<\s*SYS\s*>>"),
    re.compile(r"(?i)<\|im_start\|>\s*system"),
    re.compile(r"(?i)###\s*(?:Instruction|System|Human|Assistant):"),
]

_EXFILTRATION_PATTERNS = [
    re.compile(
        r"!\[.*?\]\(https?://[^\s)]+?[?&](?:token|secret|key|pwd|password|session|exfil)=[^\s)]+?\)"
    ),
    re.compile(r"(?i)\bjavascript:[^\s\"'>]+"),
]


class PromptInjectionPolicy(BasePolicy):
    """Detects adversarial prompt injections and delimiter hijacking."""

    name: str = "injection-scan"
    description: str = (
        "Scans for instruction overrides, jailbreak phrases, delimiter hijacking, and exfiltration."
    )
    supported_hooks: ClassVar[set[PolicyHook]] = {
        PolicyHook.INPUT,
        PolicyHook.TOOL_CALL,
    }

    def _scan_text(self, text: str) -> list[str]:
        violations: list[str] = []

        for p in _OVERRIDE_PATTERNS:
            if p.search(text):
                violations.append(f"Instruction override pattern detected: '{p.pattern}'")

        for p in _DELIMITER_PATTERNS:
            if p.search(text):
                violations.append(f"System delimiter hijacking pattern detected: '{p.pattern}'")

        for p in _EXFILTRATION_PATTERNS:
            if p.search(text):
                violations.append(f"Suspicious exfiltration vector detected: '{p.pattern}'")

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
        """Evaluate data for adversarial injections."""
        violations: list[str] = []
        self._scan_recursive(data, violations)

        if violations:
            return PolicyResult(
                passed=False,
                action=PolicyAction.BLOCK.value,
                modified_data=None,
                violations=violations,
                metadata={
                    "violation_count": len(violations),
                    "blocked_by": self.name,
                },
            )

        return PolicyResult(
            passed=True,
            action=PolicyAction.ALLOW.value,
            modified_data=data,
            violations=[],
            metadata={"status": "clean"},
        )
