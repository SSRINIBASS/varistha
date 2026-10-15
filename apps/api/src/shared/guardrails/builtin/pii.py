"""PII Redaction Guardrail Policy."""

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

_EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_IP_PATTERN = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
)
_API_KEY_PATTERN = re.compile(
    r"(?i)\b(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9]{10,}|var_[A-Za-z0-9]{24,})\b"
)
_BEARER_PATTERN = re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9\-_.=]{20,})\b")
_CANDIDATE_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def _luhn_check(digits_str: str) -> bool:
    """Verify numeric string against Luhn checksum algorithm."""
    clean = re.sub(r"\D", "", digits_str)
    if not 13 <= len(clean) <= 19:
        return False
    digits = [int(d) for d in clean]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


class PIIRedactionPolicy(BasePolicy):
    """Detects and redacts sensitive PII from text, dictionaries, and lists."""

    name: str = "pii-redact"
    description: str = (
        "Redacts emails, phone numbers, credit card numbers, SSNs, API keys, and IPv4 addresses."
    )
    supported_hooks: ClassVar[set[PolicyHook]] = {
        PolicyHook.INPUT,
        PolicyHook.OUTPUT,
        PolicyHook.TOOL_CALL,
    }

    def _redact_text(self, text: str) -> tuple[str, dict[str, int]]:
        counts: dict[str, int] = {
            "email": 0,
            "phone": 0,
            "ssn": 0,
            "card": 0,
            "api_key": 0,
            "ip": 0,
        }

        # 1. Bearer tokens & API keys
        def _bearer_sub(m: re.Match[str]) -> str:
            counts["api_key"] += 1
            return f"{m.group(1)}[REDACTED_API_KEY]"

        text = _BEARER_PATTERN.sub(_bearer_sub, text)

        def _key_sub(m: re.Match[str]) -> str:
            counts["api_key"] += 1
            return "[REDACTED_API_KEY]"

        text = _API_KEY_PATTERN.sub(_key_sub, text)

        # 2. Email
        def _email_sub(m: re.Match[str]) -> str:
            counts["email"] += 1
            return "[REDACTED_EMAIL]"

        text = _EMAIL_PATTERN.sub(_email_sub, text)

        # 3. SSN
        def _ssn_sub(m: re.Match[str]) -> str:
            counts["ssn"] += 1
            return "[REDACTED_SSN]"

        text = _SSN_PATTERN.sub(_ssn_sub, text)

        # 4. Credit cards with Luhn verification
        def _card_sub(m: re.Match[str]) -> str:
            val = m.group(0)
            if _luhn_check(val):
                counts["card"] += 1
                return "[REDACTED_CARD]"
            return val

        text = _CANDIDATE_CARD_PATTERN.sub(_card_sub, text)

        # 5. Phone numbers
        def _phone_sub(m: re.Match[str]) -> str:
            counts["phone"] += 1
            return "[REDACTED_PHONE]"

        text = _PHONE_PATTERN.sub(_phone_sub, text)

        # 6. IPv4
        def _ip_sub(m: re.Match[str]) -> str:
            counts["ip"] += 1
            return "[REDACTED_IP]"

        text = _IP_PATTERN.sub(_ip_sub, text)

        return text, counts

    def _redact_recursive(self, item: Any, agg: dict[str, int]) -> Any:
        if isinstance(item, str):
            redacted, counts = self._redact_text(item)
            for k, v in counts.items():
                agg[k] += v
            return redacted
        elif isinstance(item, dict):
            new_dict: dict[str, Any] = {}
            for k, v in item.items():
                new_dict[k] = self._redact_recursive(v, agg)
            return new_dict
        elif isinstance(item, list):
            return [self._redact_recursive(v, agg) for v in item]
        return item

    async def evaluate(self, data: Any, context: PolicyContext) -> PolicyResult:
        """Scan and redact PII patterns from data."""
        agg: dict[str, int] = {
            "email": 0,
            "phone": 0,
            "ssn": 0,
            "card": 0,
            "api_key": 0,
            "ip": 0,
        }
        modified = self._redact_recursive(data, agg)
        total_redactions = sum(agg.values())

        if total_redactions > 0:
            types_found = [k for k, v in agg.items() if v > 0]
            return PolicyResult(
                passed=True,
                action=PolicyAction.REDACT.value,
                modified_data=modified,
                violations=[],
                metadata={
                    "total_redactions": total_redactions,
                    "redaction_types": types_found,
                    "counts": agg,
                },
            )

        return PolicyResult(
            passed=True,
            action=PolicyAction.ALLOW.value,
            modified_data=data,
            violations=[],
            metadata={"total_redactions": 0},
        )
